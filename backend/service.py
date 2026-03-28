from pydantic import BaseModel,  Field
from database import Database, DatabaseRedis
from datetime import datetime
import uuid
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
    """ Returns: first_name, last_name """
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
    content = {
      'first_name': self.__first_name,
      'last_name': self.__last_name,
      'email': self.__email,
      'is_email_verified': self.__is_email_verified,
      'created_at': datetime.fromtimestamp(self.__created_at)
    }
    return content
  

  def set_name(self, first_name:str, last_name:str):
    # нужна валидация на спец символы и прочее для предотвращения траблов с бд
    from pydantic import field_validator

    class UserName(BaseModel):
      name: str = Field(..., min_length=2)

      @field_validator('name')
      @classmethod
      def abc(cls, v:str) ->str:
        if not all(char.isalpha() or char.isspace() for char in v):
          raise ValueError('Имя должно содержать только буквы и пробелы')
        return v.title()

    self.__first_name = first_name
    self.__last_name = last_name
    self.__db.change_userName_by_id(self.__id,self.__first_name, self.__last_name)


  def chek_auth(self, password:str):
    """Метод проверяет авторизацию и генерирует ответ на фронт"""
    try:
      response = self.__db.check_user(self.__email, password)

      match response:
        case 0:
          self.__token = str(uuid.uuid4())
          print("Генерируем токен: ", self.__token)
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
    private_key_pem: str = Field(..., description="Приватный ключ в формате PEM (Base64 строка)")
    public_key_pem: str = Field(..., description="Публичный ключ в формате PEM (Base64 строка)")


class SignatureUNEP:  
    """
    Класс для реализации функционала УНЭП: 
    генерация ключей, подпись хэша и валидация.
    """
    
    def __init__(self, email: str, db: Database=None, flag_pg: bool = False):
        self.__email = email
        self.__db = db
        self.__flag_pg = flag_pg

    def generate_user_keys(self) -> KeyPair:
        """
        Генерирует пару ключей Ed25519 для пользователя.
        Ключи возвращаются в формате PEM (Base64 строки).
        """
        # Генерация приватного ключа
        private_key = ed25519.Ed25519PrivateKey.generate()
        
        # Сериализация приватного ключа
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        # Генерация и сериализация публичного ключа
        public_key = private_key.public_key()
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        return KeyPair(private_key_pem=priv_pem, public_key_pem=pub_pem)

    def sign_document_hash(self, doc_hash: str, private_key_pem: str) -> str:
        """
        Шифрует (подписывает) хэш документа приватным ключом.
        doc_hash: SHA-256 хэш документа в hex или строке.
        """
        try:
            # Загружаем приватный ключ из PEM
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            
            # Подписываем данные (хэш)
            # В Ed25519 подпись идет сразу по данным, хэширование встроено
            signature = private_key.sign(doc_hash.encode('utf-8'))
            
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            print(f"[ERROR] Signing failed: {e}")
            raise ValueError("Ошибка при создании подписи")

    def verify_signature(self, doc_hash: str, signature_b64: str, public_key_pem: str) -> bool:
        """
        Валидация подписи: декодирование хэша по публичному ключу 
        и сравнение с исходным хэшем.
        """
        try:
            # Загружаем публичный ключ
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )
            
            # Декодируем подпись из base64
            signature = base64.b64decode(signature_b64)
            
            # Проверка. Если подпись неверна, метод verify выбросит InvalidSignature
            public_key.verify(signature, doc_hash.encode('utf-8'))
            return True
        except Exception as e:
            print(f"[INFO] Signature verification failed: {e}")
            return False

    def save_keys_to_db(self, keys: KeyPair) -> bool:
        """Пример интеграции с БД (без реализации подключения)"""
        if self.__db:
            # Логика сохранения в Postgres (например, в таблицу user_keys)
            
            pass
        return True