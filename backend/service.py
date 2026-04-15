from pydantic import BaseModel,  Field
from database import Database, DatabaseRedis
from datetime import datetime, timezone
import uuid
import re
import hashlib
# статусы ответов на фронт:
SUCCESS_STATUS = 0              # 0 - успешный вход
INVALID_CREDENTIALS_STATUS = 2  # 2 - логин или пароль не верные или совпадают
DB_CONNECTION_ERROR_STATUS = 3  # 3 - нет связи или ошибка с бд
GENERAL_ERROR_STATUS = 4        # 4 - иная ошибка

class User:

    def __init__(self, email:str, db: Database = None, db_redis: DatabaseRedis = None, flag_pg: bool = False):
        self.__email = email
        self.__db = db
        self.__db_redis = db_redis

        #print("Инициализация User: ", self.__email)
        # Если флаг установлен, то загружаем данные из PostgreSQL, что бы не делать лишних запросов при каждом действии
        if flag_pg:
            __user = self.__db.get_user_by_email(self.__email)
            self.__id = __user['id']
            self.__first_name = __user['first_name']
            self.__last_name = __user['last_name']
            self.__is_email_verified = __user['is_email_verified']
            self.__created_at = __user['created_at']

        self.__token = self.__get_token_to_redis()
        self.__session_active = bool(self.__token)


    def __get_token_to_redis(self) -> str | None: 
        try: 
            return self.__db_redis.get_token_by_email(self.__email)
        except Exception as ex:
            print("[ERROR] Exception in __get_token_to_redis: ", ex)
        return None
    
    def get_name(self):
        """ 
        Returns:
            first_name, last_name
        """
        return self.__first_name, self.__last_name
  
    def get_email(self) -> str:
        return self.__email
    
    def get_session_status(self) -> bool:
        return self.__session_active
    
    def get_is_email_verified(self)-> bool:
        return self.__is_email_verified

    def get_created_at(self) -> datetime:
        return datetime.fromtimestamp(self.__created_at)
  
    def get_all_info(self) -> dict:
        """
        Возвращает всю информацию о пользователе в виде словаря\n
        Returns:  first_name, last_name, email, is_email_verified, created_at
        """
        content = {
        'first_name': self.__first_name,
        'last_name': self.__last_name,
        'email': self.__email,
        'is_email_verified': self.__is_email_verified,
        'created_at': self.__created_at,
        'public_key': self.__db.get_public_key_by_email(self.__email) if self.__db.get_public_key_by_email(self.__email) is not None else "Нет ключа"
        }
        return content
  
    def set_name(self, first_name: str, last_name: str) ->bool:
        NAME_REGEX = re.compile(r"^[a-zA-Zа-яА-ЯёЁ\s-]+$")
        # 1. Валидация
        for name_part, label in [(first_name, "Имя"), (last_name, "Фамилия")]:
            if not name_part or len(name_part) < 2:
                return False          
            if not NAME_REGEX.match(name_part):
                return False

        # 2. Форматирование (опционально)
        formatted_first = first_name.strip().title()
        formatted_last = last_name.strip().title()

        # 3. Работа с БД
        try:
            # Сначала пробуем обновить БД
            self.__db.change_userName_by_id(self.__id, formatted_first, formatted_last)
            
            print(f"[INFO] User {self.__email} name updated in DB: {formatted_first} {formatted_last}")
            # Если БД не упала, обновляем состояние объекта
            self.__first_name = formatted_first
            self.__last_name = formatted_last
            return True
        except Exception as ex:
            print(f"[ERROR] Database update failed: {ex}")
            return False
      

    def chek_auth(self, password:str):
        """Метод проверяет авторизацию и генерирует ответ на фронт"""
        try:
            response = self.__db.check_user(self.__email, password)

            match response:
                case 0:
                    self.__token = str(uuid.uuid4())
                    if self.__db_redis.create_session(self.__email, self.__token):
                        self.__session_active = True
                        return {
                        "status" : SUCCESS_STATUS,
                        "token": self.__token,
                        "message": "Успешный вход!"
                        }
                    else:
                        return {
                        "status" : DB_CONNECTION_ERROR_STATUS,
                        "token": -1,
                        "message": "Проблемы с созданием сессии."
                        }
                
                case 2:
                    return {
                        "status" : INVALID_CREDENTIALS_STATUS,
                        "token": -1,
                        "message": "Не верный логин или пароль."
                    }
                    
                case 3:
                    return{
                    "status" : DB_CONNECTION_ERROR_STATUS,
                    "token": -1,
                    "message": "Проблемы с базой данных."
                    }
                
                case _:
                    return {
                    "status" : GENERAL_ERROR_STATUS,
                    "token": -1,
                    "message": response
                    }
        except Exception as exept:
            print("[ERROR] Exception in chek_auth: ", exept)
            return {
                "status" : GENERAL_ERROR_STATUS,
                "token": -1,
                "message": exept
            }



# Модели для валидации данных через Pydantic
class KeyPair(BaseModel):
    private_key: str
    public_key: str


import gostcrypto
import os
import base64
from asn1crypto import cms, core, x509, algos
from asn1crypto.core import SetOf
from typing import Any

class SignatureUNEP:  
    """
    Класс для реализации функционала УНЭП: 
    генерация ключей, подпись хэша и валидация.
    """
    
    def __init__(self, email: str, db: Database):
        self.__email = email
        self.__db = db

        self.__curve_params = gostcrypto.gostsignature.CURVES_R_1323565_1_024_2019[
            'id-tc26-gost-3410-2012-256-paramSetB'
        ]
        self.__sign_obj = gostcrypto.gostsignature.new(
            gostcrypto.gostsignature.MODE_256, 
            self.__curve_params
        )

    def __build_signed_attrs(self, message_digest: bytes, public_key: bytes | None = None) -> bytes:
        """Формирует DER-кодированный signedAttrs по требованиям 63-ФЗ + ГОСТ Р 34.11-2012"""
        message_digest = bytes(message_digest)
        if not isinstance(message_digest, bytes) or len(message_digest) != 32:
            raise ValueError("message_digest должен быть 32-байтным хэшем streebog256")

        if public_key is not None:
            public_key = bytes(public_key)
            if len(public_key) != 64:
                raise ValueError("public_key должен быть 64 байта для ГОСТ 256")

        # 1. content-type = id-data
        content_type_attr = cms.CMSAttribute({
            'type': cms.CMSAttributeType('1.2.840.113549.1.9.3'),   # content-type
            'values': [cms.ContentType('1.2.840.113549.1.7.1')]      # id-data
        })

        # 2. message-digest
        message_digest_attr = cms.CMSAttribute({
            'type': cms.CMSAttributeType('1.2.840.113549.1.9.4'),
            'values': [core.OctetString(message_digest)]
        })

        signing_time = datetime.now(timezone.utc)
        # 3. signing-time (рекомендуется)
        signing_time_attr = cms.CMSAttribute({
            'type': cms.CMSAttributeType('1.2.840.113549.1.9.5'),
            'values': [cms.Time({'utc_time': signing_time})]
        })

        attrs_list = [content_type_attr, message_digest_attr, signing_time_attr]

        if public_key is not None:
            # Нестандартное решение: добавляем публичный ключ в signedAttrs под кастомным OID,
            # чтобы проверка подписи была независима от аккаунта и БД.
            public_key_attr = cms.CMSAttribute({
                'type': cms.CMSAttributeType(self.EMBEDDED_PUBLIC_KEY_OID),
                'values': [core.OctetString(public_key)]
            })
            attrs_list.append(public_key_attr)
        # атрибуты уже идут в порядке возрастания OID → DER будет каноническим

        class SignedAttributes(SetOf):
            _child_spec = cms.CMSAttribute

        signed_attrs = SignedAttributes(attrs_list)
        return signed_attrs.dump()   # <-- DER bytes, которые потом хэшируются

    def hash_document(self, document:str, encode_flag:bool = True) -> bytes:
        """Получение хэша строки по алгоритму ГОСТ Р 34.11-2012 (стрибог)"""
        try:
            if encode_flag:
                document = document.encode('utf-8')
            hash_obj = gostcrypto.gosthash.new('streebog256', data=document)
            return hash_obj.digest()
        except Exception as e:
            print(f"[ERROR] Hashing failed: {e}")
            return None

    def __save_keys_to_db(self, keys: KeyPair) -> bool:
        try:
            self.__db.insert_keys_by_email(self.__email, keys.public_key, keys.private_key)
            return True
        except Exception as e:
            print(f"[ERROR] Saving keys to DB failed: {e}")
            raise ValueError("Ошибка при сохранении ключей в базу данных")

    def generate_user_keys(self) -> str | None:
        """
        Генерирует пару ключей гост 34.11-2012 для пользователя.
        Ключи сохраняются в формате base64
        """
        try:
            #if self.__db.get_public_key_by_email(self.__email) is not None:
            #    print(f"[INFO] User {self.__email} already has keys, skipping generation.")
            #    return None
            
            q = self.__curve_params['q']

            while True:
                d = (int.from_bytes(os.urandom(32), 'big') % (q -1)) + 1
                if 0 < d < q:
                    private_key = d.to_bytes(32, 'big')
                    break
            public_key = self.__sign_obj.public_key_generate(private_key)

            if len(private_key) != 32 or len(public_key) != 64:
                raise ValueError("Generated keys have incorrect length")
            
            # Проверка на соответствие ключей
            digest = self.hash_document("testqwertyuioqwertyuio"*10)

            digest_attrs = self.__build_signed_attrs(digest, public_key=public_key)
            digest_attrs_hash = self.hash_document(digest_attrs, encode_flag=False)

            #print(f"[DEBUG] digest_attrs_hash: {digest_attrs_hash}")
            #print(f"[DEBUG] digest: {digest}")

            signature = self.__sign_obj.sign(private_key, digest_attrs_hash)

            if not self.__sign_obj.verify(public_key, digest_attrs_hash, signature):
                raise ValueError("Signature verification failed with generated keys")

            print(f"[INFO] Keys generated successfully for user {self.__email}")
            private_key_b64 = base64.b64encode(private_key).decode()
            public_key_b64 = base64.b64encode(public_key).decode()

            #self.__save_keys_to_db(KeyPair(private_key=private_key_b64, public_key=public_key_b64))
            
            return  public_key_b64, private_key_b64
        except Exception as e:
            print(f"[ERROR] Key generation failed: {e}")
            return None


    def signed_hash(self, document: str, private_key_b64: str) -> dict:
        """
        Шифрует (подписывает) signedAttrs документа приватным ключом.
        
        """
        try:         
            #private_key_b64 = self.__db.get_private_key_by_email(self.__email)  
            if private_key_b64 is None:
                raise ValueError("Пользователь не имеет приватного ключа для подписи")
            private_key = base64.b64decode(private_key_b64)
            public_key = self.__sign_obj.public_key_generate(private_key)
            
            doc_hash = self.hash_document(document)
            signed_attrs_der = self.__build_signed_attrs(doc_hash, public_key=public_key)
            signed_attrs_hash = self.hash_document(signed_attrs_der, encode_flag=False)
            
            signature = self.__sign_obj.sign(bytearray(private_key), signed_attrs_hash)

            print(f"[INFO] Document signed successfully for user {self.__email}")


            return {
                'signature': signature,           # raw bytes подписи
                'signed_attrs_der': signed_attrs_der,  # DER signedAttrs (ОБЯЗАТЕЛЬНО для CMS)
                'content_hash': doc_hash      # на всякий случай
            }
        except Exception as e:
            print(f"[ERROR] Signing failed: {e}")
            raise ValueError("Ошибка при создании подписи")

    def verify_signature(self, doc_hash: str, signature: str, public_key: str) -> bool:
        """
        Валидация подписи: декодирование хэша по публичному ключу 
        и сравнение с исходным хэшем.
        """
        try:
            return self.__sign_obj.verify(base64.b64decode(public_key), doc_hash, signature)
        except Exception as e:
            print(f"[ERROR] Signature verification failed: {e}")
            return False

    def __extract_cms_attrs(self, signed_attrs: cms.CMSAttributes) -> list[dict[str, Any]]:
        """Преобразует CMS signedAttrs в удобный список словарей для логирования/возврата."""
        attrs_list = []

        for attr in signed_attrs:
            attr_type_obj = attr['type']
            attr_values = attr['values']

            if hasattr(attr_type_obj, 'dotted'):
                oid = attr_type_obj.dotted
            else:
                oid = str(attr_type_obj)

            attr_name = attr_type_obj.native if hasattr(attr_type_obj, 'native') else oid

            normalized_values = []
            for value in attr_values:
                native_value = value.native if hasattr(value, 'native') else value

                # Нестандартное решение: дублируем бинарные значения в hex,
                # чтобы было удобно читать атрибуты digest/подписи в логах.
                if isinstance(native_value, bytes):
                    normalized_values.append({
                        'type': 'bytes',
                        'hex': native_value.hex(),
                        'base64': base64.b64encode(native_value).decode(),
                    })
                elif isinstance(native_value, datetime):
                    normalized_values.append({
                        'type': 'datetime',
                        'value': native_value.isoformat(),
                    })
                else:
                    # Нестандартное решение: для неизвестных объектов делаем str(),
                    # чтобы attrs всегда были JSON-serializable для API-ответа.
                    json_safe_value = native_value
                    if not isinstance(native_value, (str, int, float, bool, type(None), list, dict)):
                        json_safe_value = str(native_value)

                    normalized_values.append({
                        'type': type(native_value).__name__,
                        'value': json_safe_value,
                    })

            attrs_list.append({
                'name': attr_name,
                'oid': oid,
                'values': normalized_values,
            })

        return attrs_list

    def __extract_embedded_public_key(self, signed_attrs: cms.CMSAttributes) -> bytes | None:
        """Извлекает публичный ключ из signedAttrs по кастомному OID (если присутствует)."""
        for attr in signed_attrs:
            attr_oid = attr['type'].dotted if hasattr(attr['type'], 'dotted') else str(attr['type'])
            if attr_oid == self.EMBEDDED_PUBLIC_KEY_OID:
                key_bytes = attr['values'][0].native
                if not isinstance(key_bytes, bytes) or len(key_bytes) != 64:
                    raise ValueError("Встроенный публичный ключ в signedAttrs невалиден")
                return key_bytes
        return None

    def verify_cms_container(
        self,
        cms_signature_bytes: bytes,
        signed_document: bytes | str,
        public_key_b64: str | None = None,
        allow_db_fallback: bool = True,
    ) -> dict[str, Any]:
        """
        Проверяет detached CMS/PKCS#7 подпись и извлекает signedAttrs.

        Параметры:
            cms_signature_bytes: DER-байты контейнера (.sig),
            signed_document: подписанный документ (bytes или str),
            public_key_b64: публичный ключ в base64; если не передан,
                            пробуем получить из БД по email.

        Возвращает именованный словарь с результатами проверки и атрибутами.
        """
        try:
            if not isinstance(cms_signature_bytes, (bytes, bytearray)):
                raise ValueError("cms_signature_bytes должен быть bytes/bytearray")
            cms_signature_bytes = bytes(cms_signature_bytes)

            if isinstance(signed_document, str):
                document_bytes = signed_document.encode('utf-8')
            elif isinstance(signed_document, (bytes, bytearray)):
                document_bytes = bytes(signed_document)
            else:
                raise ValueError("signed_document должен быть bytes или str")

            content_info = cms.ContentInfo.load(cms_signature_bytes)
            if content_info['content_type'].native != 'signed_data':
                raise ValueError("CMS контейнер не содержит signed_data")

            signed_data: cms.SignedData = content_info['content']
            signer_infos = signed_data['signer_infos']
            if len(signer_infos) == 0:
                raise ValueError("В CMS отсутствует signer_infos")

            signer_info: cms.SignerInfo = signer_infos[0]
            signed_attrs = signer_info['signed_attrs']
            raw_signature = signer_info['signature'].native

            embedded_public_key = self.__extract_embedded_public_key(signed_attrs)
            public_key_source = 'signed_attrs'
            if embedded_public_key is not None:
                public_key = embedded_public_key
            else:
                public_key_source = 'external'
                if not public_key_b64 and allow_db_fallback:
                    public_key_b64 = self.__db.get_public_key_by_email(self.__email)
                if not public_key_b64:
                    raise ValueError("Не удалось получить публичный ключ для проверки подписи")
                public_key = base64.b64decode(public_key_b64)

            digest_oid = signer_info['digest_algorithm']['algorithm'].dotted
            sign_oid = signer_info['signature_algorithm']['algorithm'].dotted

            attrs_list = self.__extract_cms_attrs(signed_attrs)

            # Вытаскиваем message-digest из signedAttrs.
            message_digest_attr = next(
                (attr for attr in signed_attrs if attr['type'].native == 'message_digest'),
                None
            )
            if message_digest_attr is None:
                raise ValueError("В signedAttrs отсутствует обязательный атрибут message-digest")

            cms_message_digest = message_digest_attr['values'][0].native
            document_hash = self.hash_document(document_bytes, encode_flag=False)
            content_hash_match = document_hash == cms_message_digest

            expected_ski = hashlib.sha1(public_key).digest()
            sid = signer_info['sid']
            sid_match = False
            sid_type = sid.name
            if sid_type == 'subject_key_identifier':
                sid_match = sid.chosen.native == expected_ski

            # Нестандартное решение: проверяем подпись по двум DER-представлениям атрибутов.
            # Причина: в ряде CMS-реализаций signedAttrs может сериализоваться как
            # контекстно-тегированный блок ([0]) или как "чистый" SET OF.
            # В вашем create_cms_container подпись рассчитывается над "чистым" SET OF,
            # поэтому сначала проверяем untag(), затем fallback на dump().
            signed_attrs_der_untagged = signed_attrs.untag().dump()
            signed_attrs_hash_untagged = self.hash_document(signed_attrs_der_untagged, encode_flag=False)
            signature_valid = self.__sign_obj.verify(public_key, signed_attrs_hash_untagged, raw_signature)

            verification_mode = 'untagged_signed_attrs'
            if not signature_valid:
                signed_attrs_der_tagged = signed_attrs.dump()
                signed_attrs_hash_tagged = self.hash_document(signed_attrs_der_tagged, encode_flag=False)
                signature_valid = self.__sign_obj.verify(public_key, signed_attrs_hash_tagged, raw_signature)
                verification_mode = 'tagged_signed_attrs'

            digest_oid_match = digest_oid == self.GOST_3411_2012_256_OID
            sign_oid_match = sign_oid == '1.2.643.7.1.1.3.2'

            is_valid = all([
                signature_valid,
                content_hash_match,
                digest_oid_match,
                sign_oid_match,
                sid_match,
            ])

            print("[INFO] Атрибуты CMS подписи:")
            for idx, attr in enumerate(attrs_list, start=1):
                print(f"  {idx}. {attr['name']} ({attr['oid']})")
                for value in attr['values']:
                    if value['type'] == 'bytes':
                        print(f"     - bytes.hex: {value['hex']}")
                    else:
                        print(f"     - {value['value']}")

            result = {
                'is_valid': is_valid,
                'checks': {
                    'signature_valid': signature_valid,
                    'content_hash_match': content_hash_match,
                    'digest_oid_match': digest_oid_match,
                    'sign_oid_match': sign_oid_match,
                    'sid_match': sid_match,
                },
                'verification_mode': verification_mode,
                'signer_info': {
                    'sid_type': sid_type,
                    'digest_oid': digest_oid,
                    'signature_oid': sign_oid,
                    'signature_hex': raw_signature.hex(),
                    'public_key_source': public_key_source,
                },
                'attrs': attrs_list,
            }

            print(f"[INFO] Итог проверки CMS: is_valid={is_valid}, mode={verification_mode}")
            return result

        except Exception as e:
            print(f"[ERROR] CMS verification failed: {e}")
            return {
                'is_valid': False,
                'checks': {
                    'signature_valid': False,
                    'content_hash_match': False,
                    'digest_oid_match': False,
                    'sign_oid_match': False,
                    'sid_match': False,
                },
                'verification_mode': 'error',
                'signer_info': {},
                'attrs': [],
                'error': str(e),
            }
        

# ОИДы для ГОСТ (обязательны для валидации)
    GOST_3411_2012_256_OID = '1.2.643.7.1.1.2.2'
    GOST_3410_2012_256_OID = '1.2.643.7.1.1.1.1'
    EMBEDDED_PUBLIC_KEY_OID = '1.2.643.7.1.0.99999.1'

    def create_cms_container(
        self,
        signed_attrs_der: bytes,
        raw_signature: bytes,
        public_key: bytes,
        output_filename: str = "document.sig"
    ) -> str:
        """
        Формирует валидный CMS/PKCS#7 SignedData контейнер (.sig)
        по требованиям 63-ФЗ и ГОСТ Р 34.10-2012 / 34.11-2012 (УНЭП).

        Параметры:
            signed_attrs_der  — DER signedAttrs из sign_document_hash
            raw_signature     — сырая подпись из sign_document_hash
            public_key   — ключ в формате base64
            output_filename   — имя выходного файла .sig

        Возвращает: путь к созданному .sig файлу
        """

        signed_attrs_der = bytes(signed_attrs_der)
        raw_signature = bytes(raw_signature)
        if not isinstance(signed_attrs_der, bytes) or len(signed_attrs_der) < 30:
            raise ValueError("signed_attrs_der должен быть валидным DER signedAttrs")
        if not isinstance(raw_signature, bytes) or len(raw_signature) not in (64, 128):
            raise ValueError("raw_signature должен быть 64 или 128 байт (GOST 256/512)")

        try:
            public_key = base64.b64decode(public_key)
            ski = hashlib.sha1(public_key).digest()

            # Алгоритмы ГОСТ (256-бит — как в вашем классе)
            digest_algo = {'algorithm': '1.2.643.7.1.1.2.2'}     # gost3411-2012-256
            sign_algo = {'algorithm': '1.2.643.7.1.1.3.2'}   # gost3410-2012-256

            signed_attrs = cms.CMSAttributes.load(signed_attrs_der)
            
            # SignerInfo
            signer_info = cms.SignerInfo({
                'version': 3,
                'sid': cms.SignerIdentifier({
                    'subject_key_identifier': ski
                }),
                'digest_algorithm': digest_algo,
                'signed_attrs': signed_attrs,
                'signature_algorithm': sign_algo,
                'signature': raw_signature,
            })
            encap_content_info = {
                    'content_type': 'data',   
                    'content': None       # 1.2.840.113549.1.7.1
                }
            # SignedData (detached signature)
            signed_data = cms.SignedData({
                'version': 1,
                'digest_algorithms': [digest_algo],
                'encap_content_info': encap_content_info,  # eContent отсутствует → detached
                'signer_infos': [signer_info],
            })

            # Обёртка ContentInfo (стандартный формат .sig в РФ)
            content_info = cms.ContentInfo({
                'content_type': 'signed_data',
                'content': signed_data,
            })

            cms_der = content_info.dump()

            # Сохраняем в файл
            with open(output_filename, "wb") as f:
                f.write(cms_der)

            print(f"[INFO] CMS-контейнер успешно создан: {output_filename} ({len(cms_der)} байт)")
            return cms_der

        except Exception as e:
            print(f"[ERROR] CMS creation failed: {e}")
            raise ValueError("Ошибка при формировании CMS-контейнера (.sig)") from e
