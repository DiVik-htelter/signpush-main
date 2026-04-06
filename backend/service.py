from pydantic import BaseModel,  Field
from database import Database, DatabaseRedis
from datetime import datetime
import uuid
import re
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


    async def __get_token_to_redis(self) -> str | None: 
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
        'created_at': self.__created_at
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


import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Модели для валидации данных через Pydantic
class KeyPair(BaseModel):
    private_key: str
    public_key: str


import gostcrypto
import os


# сейчас данные (ключи) ходят туда сюда на прямую, для защиты
# нужно сразу сохранять их в бд и получать только по токену сессии (а не email)
# 

class SignatureUNEP:  
    """
    Класс для реализации функционала УНЭП: 
    генерация ключей, подпись хэша и валидация.
    """
    
    def __init__(self, email: str, db: Database = None, db_redis: DatabaseRedis = None):
        self.__email = email
        self.__db = db
        self.__db_redis = db_redis

        self.__curve_params = gostcrypto.gostsignature.CURVES_R_1323565_1_024_2019[
            'id-tc26-gost-3410-2012-256-paramSetB'
        ]
        self.__sign_obj = gostcrypto.gostsignature.new(
            gostcrypto.gostsignature.MODE_256, 
            self.__curve_params
        )

    def hash_document(self, document:str = "test document") -> bytes:
        """Получение хэша строки по алгоритму ГОСТ Р 34.11-2012 (стрибог)"""
        try:
            document = document.encode('utf-8') 
            hash_obj = gostcrypto.gosthash.new('streebog256', data=document)
            return hash_obj.digest()
        except Exception as e:
            print(f"[ERROR] Hashing failed: {e}")
            return None

    async def __save_keys_to_db(self, keys: KeyPair) -> bool:
        try:
            self.__db.insert_keys_by_email(self.__email, keys.private_key, keys.public_key)
            return True
        except Exception as e:
            print(f"[ERROR] Saving keys to DB failed: {e}")
            raise ValueError("Ошибка при сохранении ключей в базу данных")

    def generate_user_keys(self) -> KeyPair | None:
        """
        Генерирует пару ключей гост 34.11-2012 для пользователя.
        Ключи сохраняются в формате base64
        """
        try:
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
            digest = self.hash_document("test")
            signature = self.__sign_obj.sign(private_key, digest)

            if not self.__sign_obj.verify(public_key, digest, signature):
                raise ValueError("Signature verification failed with generated keys")

            print(f"[INFO] Keys generated successfully for user {self.__email}")
            private_key_b64 = base64.b64encode(private_key).decode()
            public_key_b64 = base64.b64encode(public_key).decode()

            self.__db.insert_keys_by_email(self.__email, private_key_b64, public_key_b64)
            return  public_key_b64
        except Exception as e:
            print(f"[ERROR] Key generation failed: {e}")
            return None


    async def sign_document_hash(self, doc_hash: str) -> str:
        """
        Шифрует (подписывает) хэш документа приватным ключом.
        doc_hash: хэш документа.
        """
        try: 
            if self.__db_redis.get_token_by_email(self.__email) is None:
                raise ValueError("Пользователь не авторизован. Нет активной сессии.")
            
            private_key_b64 = self.__db.get_private_key_by_email(self.__email)  
            private_key = base64.b64decode(private_key_b64)

            signature = self.__sign_obj.sign(private_key, doc_hash)
            print(f"[INFO] Document signed successfully for user {self.__email}")
            return signature
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


        
    def generate_sign_file(self):
        try:
            pass
        except Exception as e:
            print(f"[ERROR] Generating sign file failed: {e}")
            raise ValueError("Ошибка при генерации файла подписи")
        