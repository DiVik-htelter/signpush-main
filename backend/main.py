import uvicorn
from time import time
from hashlib import sha256
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, Header
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Database, DatabaseRedis
from pdf_signer import add_signature_to_pdf, validate_signature_params
import service
from service import SignatureUNEP


app = FastAPI(
    title="SignPush API",
    description="API для управления документами и электронной подписи PDF файлов",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
db = Database()
db_redis = DatabaseRedis()

# Разрешенные источники
origins = [
    "http://localhost:3000",
    "http://localhost:8000"
]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Список источников
    allow_credentials=True, # Разрешить Cookies
    allow_methods=["*"],    # Разрешить все методы (GET, POST, etc.)
    allow_headers=["*"],    # Разрешить все заголовки
)
newToken = None


def check_token_redis(db_redis: DatabaseRedis, token:str, email:str) -> bool:
    """Сопоставляет токен из запроса с токеном, хранящимся в Redis для данного email. Возвращает True, если токены совпадают, иначе False."""
    try:
        token_redis = db_redis.get_token_by_email(email)
        return token == token_redis
    except Exception as ex:
        print(f"[ERROR] Exception in check_token_redis: {ex}")
        return False

class oldUser(BaseModel):
  """
  Образ пользователя с такими данными как: \n
  mail: почта / логин\n
  password: пароль """
  mail: str = Field(
      ..., 
      description="Email пользователя (логин)",
      json_schema_extra={"example": "admin@gmail.com"}
  )
  password: str = Field(
      ..., 
      description="Пароль пользователя",
      json_schema_extra={"example": "adminadmin"}
  )
  
class AuthResponse(BaseModel):
  """Модель ответа при аутентификации"""
  status: int = Field(
      ..., 
      description="Код статуса: 0 - успешно, 2 - неверные данные, 4 - ошибка",
      json_schema_extra={"example": 0}
  )
  token: Optional[int] = Field(
      None, 
      description="Токен аутентификации (выдается при успешном входе)",
      json_schema_extra={"example": 12345678}
  )
  message: str = Field(
      ..., 
      description="Сообщение о результате аутентификации",
      json_schema_extra={"example": "Успешно!"}
  )


@app.post("/api/auth", response_model=AuthResponse, summary="Аутентификация пользователя", tags=["Аутентификация"])
async def chek_login(old_user: oldUser, token: Optional[str] = Header(None)  ):
  """
  Проверка учетных данных и выдача токена аутентификации
  
  **Коды статуса ответа:**
  - 0: Успешная аутентификация
  - 2: Неверный логин или пароль
  - 3: Ошибка подключения к базе данных
  """
  try:
    content = None
    token_redis = db_redis.get_token_by_email(old_user.mail)
    if token == token_redis:
        content = {
            'status': service.SUCCESS_STATUS,
            'token': token,
            'message': 'Добро пожаловать!'
        }
    else:
        user = service.User(email=old_user.mail, db_redis=db_redis, db=db)
        content = user.chek_auth(old_user.password)   
  except Exception as exept:
    print(f"[ERROR] Ошибка непосредственно в роуте chek_login(): {exept}") 
  
  return JSONResponse(content=content)


class Paper(BaseModel):
  id: int = Field(
      ..., 
      description="Уникальный идентификатор документа",
      json_schema_extra={"example": 1}
  )
  title: str = Field(
      ..., 
      description="Название документа",
      json_schema_extra={"example": "Контракт.pdf"}
  )
  hash: str = Field(
      ..., 
      description="SHA256 хеш документа для проверки целостности",
      json_schema_extra={"example": "a1b2c3d4e5f6..."}
  )
  base64: str = Field(
      ..., 
      description="Содержимое документа в формате Base64",
      json_schema_extra={"example": "JVBERi0xLjQKJeHo8OXo8eHo8eHo..."}
  )
  created_at: int = Field(
      ..., 
      description="Время создания документа (Unix timestamp в секундах)",
      json_schema_extra={"example": 1704067200}
  )
  email: str = Field(
      ..., 
      description="Email владельца документа",
      json_schema_extra={"example": "admin@gmail.com"}
  )

class PaperList(BaseModel):
    id: int = Field(
        ..., 
        description="Уникальный идентификатор документа",
        json_schema_extra={"example": 1}
    )
    title: str = Field(
        ..., 
        description="Название документа",
        json_schema_extra={"example": "Контракт.pdf"}
    )
    hash: str = Field(
        ..., 
        description="SHA256 хеш документа для проверки целостности",
        json_schema_extra={"example": "a1b2c3d4e5f6..."}
    )
    signing_status: str = Field(
        ..., 
        description="Статус подписания документа",
        json_schema_extra={"example": "unsigned" }
    )
    created_at: int = Field(
        ..., 
        description="Время создания документа (Unix timestamp в секундах)",
        json_schema_extra={"example": 1704067200}
    )
    email: str = Field(
        ..., 
        description="Email владельца документа",
        json_schema_extra={"example": "admin@gmail.com"}
    )

# Модель ответа
class PapersResponse(BaseModel):
  message: str = Field(
      ..., 
      description="Сообщение о количестве полученных документов",
      json_schema_extra={"example": "There are 5 paperes"}
  )
  papers: List[PaperList] = Field(
      ..., 
      description="Список документов пользователя"
  )

@app.post("/api/docs/download", tags=["Документы"], summary="Загрузка документа в бд")
async def insert_docs(paper:Paper, token: Optional[str] = Header(None)):    
    try:
        if token == db_redis.get_token_by_email(paper.email):
            flag = db.insert_doc(paper.title, paper.hash, paper.created_at, paper.base64, paper.email)
        
            content = { 
            "success": flag
            }
        else: 
           content = {
            "success": False,
            "message": "Invalid token",
            'navigate': '/login'
           }
       
    except Exception as exept:
        print(f"[ERROR] Ошибка непосредственно в роуте добавления документа: {exept}") 
    
    return JSONResponse(content=content)

@app.get(
    "/api/docs", 
    response_model=PapersResponse,
    summary="Получение списка документов",
    tags=["Документы"],
    description="Получить список всех документов пользователя по его email адресу"
)
async def get_docs(token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
  """Получение списка документов по логину""" 

  temp_token = db_redis.get_token_by_email(email)
  if token != temp_token:
      return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)  
  # если токен не валиден то логин не найдется, я не знаю нужна ли тут еще какая то проверка
  
  
  result = db.get_all_list_docs(str(email))
  total = len(result)
  message =f"There are {total} paperes"

  papers_list = [PaperList(**doc) for doc in result]

  return PapersResponse(message=message, papers=papers_list)

@app.patch( 
      "/api/docs",
        response_model=Paper,
        summary="Получение документа по ID",
        tags=["Документы"],
        description="Получить документ по его уникальному идентификатору (ID)"
)
async def get_docs_by_id(doc_id: int, token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
  """Получение документа по ID""" 

  if not check_token_redis(db_redis, token, email):
    return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

  result = db.get_document_by_id(doc_id)
  if result:
    return Paper(**result)
  else:
    return JSONResponse(content={"message": "Документ не найден"}, status_code=404)



@app.delete(
      "/api/docs",
        tags=["Документы"],
        summary="Удаление документа по ID",
        description="Удалить документ по его уникальному идентификатору (ID)"
)
async def doc_delete(doc_id:int, token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
  """Удаление документа по ID"""
  flag = False
  try:
    if not check_token_redis(db_redis, token, email):
        return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

    flag = db.delet_document_by_id(doc_id) # id документа, который автоматически выдается в базе данных 
  except Exception as ex:
    print(f"[ERROR] Ошибка при удалениии документа из БД: {ex}")
  
  content = {'status': 0,
             'message': 'Документ успешно удалён!',
             'success': flag }
  return JSONResponse(content=content)


# ============================================================================
# НОВЫЙ ENDPOINT: Подписание PDF документа
# ============================================================================

class SignatureRequest(BaseModel):
    document_id: int = Field(
        ...,
        description="ID документа для подписания",
        json_schema_extra={"example": 1},
        gt=0
    )
    signature_base64: str = Field(
        ...,
        description="Изображение подписи в Base64 формате (PNG/JPEG)",
        json_schema_extra={"example": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR..."}
    )
    page_number: int = Field(
        ...,
        description="Номер страницы документа (0-indexed, начиная с 0)",
        json_schema_extra={"example": 0},
        ge=0
    )
    x: float = Field(
        ...,
        description="Координата X на canvas для размещения подписи (в пиксельях)",
        json_schema_extra={"example": 100.5},
        ge=0
    )
    y: float = Field(
        ...,
        description="Координата Y на canvas для размещения подписи (в пиксельях)",
        json_schema_extra={"example": 150.5},
        ge=0
    )
    width: float = Field(
        ...,
        description="Ширина подписи на canvas (в пиксельях)",
        json_schema_extra={"example": 200.0},
        gt=0
    )
    height: float = Field(
        ...,
        description="Высота подписи на canvas (в пиксельях)",
        json_schema_extra={"example": 100.0},
        gt=0
    )
    login: str = Field(
        ...,
        description="Email пользователя, который подписывает документ",
        json_schema_extra={"example": "admin@gmail.com"}
    )


class SignDocumentResponse(BaseModel):
    """Модель ответа при подписании документа"""
    success: bool = Field(
        ...,
        description="Флаг успешного подписания документа",
        json_schema_extra={"example": True}
    )
    message: str = Field(
        ...,
        description="Описание результата операции",
        json_schema_extra={"example": "Документ успешно подписан и сохранён"}
    )
    new_document_id: Optional[int] = Field(
        None,
        description="ID нового подписанного документа (если успешно)",
        json_schema_extra={"example": 2}
    )
    hash: Optional[str] = Field(
        None,
        description="SHA256 хеш подписанного документа",
        json_schema_extra={"example": "a1b2c3d4e5f6..."}
    )


@app.post(
    "/api/document/sign/",
    response_model=SignDocumentResponse,
    summary="Подписание PDF документа визуальной подписью",
    tags=["Подписание документов"],
    description="Электронная подпись PDF документа с визуальным отображением подписи на странице. Процесс: 1. Получение документа из БД 2. Встраивание подписи в PDF 3. Вычисление нового хеша 4. Сохранение подписанного документа"
)
async def sign_document(request: SignatureRequest, token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
    """
    Подписывает PDF документ визуальной подписью.
    
    Процесс:
    1. Получает оригинальный документ из БД
    2. Встраивает подпись в PDF на указанной странице и позиции
    3. Вычисляет новый хеш подписанного документа
    4. Сохраняет подписанный документ как новую версию
    
    Returns:
        JSON с результатом операции и ID нового документа
    """
    try:

        if not check_token_redis(db_redis, token, email):
            return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)
       
        # Валидация параметров подписи
        valid, error_msg = validate_signature_params(
            request.page_number, request.x, request.y, 
            request.width, request.height
        )
        
        if not valid:
            return JSONResponse(
                content={
                    "success": False, 
                    "message": f"Invalid signature parameters: {error_msg}"
                },
                status_code=400
            )
        
        # Получаем оригинальный документ из БД
        doc = db.get_document_by_id(request.document_id)
        
        if not doc:
            return JSONResponse(
                content={"success": False, "message": "Документ не найден"},
                status_code=404
            )
               
        # Встраиваем подпись в PDF
        
        signed_pdf, success = add_signature_to_pdf(
            pdf_base64=doc['base64'],
            signature_base64=request.signature_base64,
            page_number=request.page_number,
            x=request.x,
            y=request.y,
            width=request.width,
            height=request.height
        )
        
        if not success:
            return JSONResponse(
                content={
                    "success": False, 
                    "message": "Ошибка при встраивании подписи в PDF"
                },
                status_code=500
            )
        
        # Вычисляем новый хеш подписанного документа
        signed_pdf_clean = signed_pdf.split('base64,')[-1] if 'base64,' in signed_pdf else signed_pdf
        new_hash = sha256(signed_pdf_clean.encode()).hexdigest()
                
        # Подготавливаем данные о подписи для сохранения
        signature_data = {
            'signature_base64': request.signature_base64,
            'page_number': request.page_number,
            'x': request.x,
            'y': request.y,
            'width': request.width,
            'height': request.height
        }
        
        # Сохраняем подписанный документ как новую версию
        new_doc_id = db.insert_signed_document(
            title=f"{doc['title']} (Подписан)",
            hash=new_hash,
            created_at=int(time()),
            base64=signed_pdf,
            email=request.login,
            original_doc_id=request.document_id,
            signer=request.login,
            signature_data=signature_data
        )
        
        if new_doc_id:
            print(f"[API] Signed document saved successfully with ID: {new_doc_id}")
            return JSONResponse(content={
                "success": True,
                "message": "Документ успешно подписан и сохранён",
                "new_document_id": new_doc_id,
                "hash": new_hash
            })
        else:
            return JSONResponse(
                content={
                    "success": False, 
                    "message": "Ошибка при сохранении подписанного документа"
                },
                status_code=500
            )
        
    except Exception as ex:
        print(f"[ERROR] Ошибка при подписании документа: {ex}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"success": False, "message": str(ex)},
            status_code=500
        )

class newUser(BaseModel):
   email:str
   password: str
   first_name:str
   last_name:str


@app.post("/api/register/", tags=["Регистрация"])
async def register_user(user: newUser):
  """Регистрация нового пользователя"""
  flag = False
  try:
    name = {
       'firstName': user.first_name,
       'lastName': user.last_name,
    }
    flag = db.insert_user(user.email, user.password, name)
    if flag:
        content = {'status': service.SUCCESS_STATUS,
               'message': 'Успешная регистрация!'}
    else:
        content = {'status': service.INVALID_CREDENTIALS_STATUS}
    
    return JSONResponse(content=content)    
  except Exception as ex:
    print(f"[ERROR] Ошибка непостредственно в роуте register_user", ex)

import base64
from fastapi.responses import Response



@app.get("/api/docs/download/", tags=["Документы"], summary="Скачивание документа по id")
async def download_docs(doc_id:int, token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
    if not check_token_redis(db_redis, token, email):
        return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

    doc = db.get_document_by_id(doc_id)
    doc_title = doc['title']
    doc = doc['base64']
    s = 'data:application/pdf;base64,' # подстрока, которую нужно удалить из base64
    if "," in doc:
        header, base64_str = doc.split(",", 1)
    else:
        base64_str = doc

    headers = {
        'Content-Disposition': f'attachment;' # добавить бы filename, но он плохо воспринимает кириллицу, имей в виду
    }
    file_bytes = base64.b64decode(base64_str)
    return Response(headers=headers, content=file_bytes)


def _normalize_base64_payload(value: str) -> str:
    """Удаляет data-url префикс и пробелы для корректного base64-decode."""
    if not value:
        return value
    if ',' in value:
        _, value = value.split(',', 1)
    return value.strip()


def _decode_key_len(key_b64: Optional[str]) -> int:
    """Возвращает длину ключа в байтах после base64-decode или -1 при ошибке."""
    if not key_b64:
        return -1
    try:
        return len(base64.b64decode(key_b64))
    except Exception:
        return -1


class SignatureUNEPRequest(BaseModel):
    document_id: int = Field(..., description="ID документа для подписи УНЭП", gt=0)


class SignatureUNEPResponse(BaseModel):
    success: bool = Field(..., description="Результат операции")
    message: str = Field(..., description="Описание результата")
    signature_base64: Optional[str] = Field(None, description="CMS контейнер подписи в base64")
    attributes: Optional[list] = Field(None, description="Signed attributes подписи")
    filename: str


class SignatureValidationUNEPRequest(BaseModel):
    document_base64: str = Field(..., description="Base64 содержимое подписанного документа")
    signature_base64: str = Field(..., description="CMS подпись в base64")
    signer_email: Optional[str] = Field(None, description="Email подписанта. Если не указан, используется текущий")


class SignatureValidationUNEPResponse(BaseModel):
    success: bool = Field(..., description="Успешность выполнения запроса")
    is_valid: bool = Field(..., description="Валидна ли подпись")
    message: str = Field(..., description="Описание результата")
    attrs: list = Field(default_factory=list, description="Извлеченные signedAttrs")
    checks: dict = Field(default_factory=dict, description="Детальные проверки")


@app.post(
    "/api/document/sign/unep/",
    tags=["Подписание документов"],
    summary="Подписание документа в формате УНЭП",
    response_model=SignatureUNEPResponse
)
async def sign_document_unep(request: SignatureUNEPRequest, token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
    if not check_token_redis(db_redis, token, email):
        return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

    try:
        doc = db.get_document_by_id(request.document_id)
        if not doc:
            return JSONResponse(content={"success": False, "message": "Документ не найден"}, status_code=404)

        if doc.get('email') != email:
            return JSONResponse(content={"success": False, "message": "Нет доступа к документу"}, status_code=403)

        signer = SignatureUNEP(email, db)
        private_key_b64 = db.get_private_key_by_email(email)
        public_key_b64 = db.get_public_key_by_email(email)

        private_len = _decode_key_len(private_key_b64)
        public_len = _decode_key_len(public_key_b64)

        # Нестандартное решение: автоисправление перепутанных местами ключей в БД.
        # В проекте исторически встречался сценарий, когда private/public сохранялись наоборот.
        if private_len == 64 and public_len == 32:
            print(f"[WARNING] Detected swapped keys for user {email}. Auto-fixing in DB.")
            private_key_b64, public_key_b64 = public_key_b64, private_key_b64
            db.insert_keys_by_email(email, public_key_b64, private_key_b64)
            private_len = _decode_key_len(private_key_b64)
            public_len = _decode_key_len(public_key_b64)

        # Валидный набор: private=32 bytes, public=64 bytes.
        if private_len != 32 or public_len != 64:
            print(f"[WARNING] Invalid key lengths for user {email}: private={private_len}, public={public_len}. Regenerating keys.")
            generated_keys = signer.generate_user_keys()
            if not generated_keys:
                return JSONResponse(content={"success": False, "message": "Не удалось сгенерировать ключи"}, status_code=500)

            public_key_b64, private_key_b64 = generated_keys
            db.insert_keys_by_email(email, public_key_b64, private_key_b64)

        document_for_sign = _normalize_base64_payload(doc['base64'])
        signed_payload = signer.signed_hash(document_for_sign, private_key_b64)
        cms_der = signer.create_cms_container(
            signed_payload['signed_attrs_der'],
            signed_payload['signature'],
            public_key_b64,
            output_filename=f"document_{request.document_id}.sig"
        )

        # Повторно разбираем подпись и возвращаем attrs, чтобы фронту было что показать.
        verify_preview = signer.verify_cms_container(
            cms_signature_bytes=cms_der,
            signed_document=document_for_sign,
            public_key_b64=public_key_b64,
        )
        filename = doc.get('title')
        return JSONResponse(content={
            "success": True,
            "message": "Документ успешно подписан УНЭП",
            "signature_base64": base64.b64encode(cms_der).decode(),
            "attributes": verify_preview.get('attrs', []),
            "filename": filename,
            }, status_code=200)

    except Exception as ex:
        print(f"[ERROR] Ошибка в sign_document_unep: {ex}")
        return JSONResponse(content={"success": False, "message": str(ex)}, status_code=500)


@app.post(
    "/api/document/verify/unep/",
    tags=["Подписание документов"],
    summary="Проверка валидности УНЭП подписи",
    response_model=SignatureValidationUNEPResponse
)
async def verify_document_unep(request: SignatureValidationUNEPRequest, token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
    if not check_token_redis(db_redis, token, email):
        return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

    try:
        signer_email = request.signer_email or email
        signer = SignatureUNEP(signer_email, db)

        normalized_doc = _normalize_base64_payload(request.document_base64)
        normalized_sig = _normalize_base64_payload(request.signature_base64)

        cms_bytes = base64.b64decode(normalized_sig)

        result = signer.verify_cms_container(
            cms_signature_bytes=cms_bytes,
            signed_document=normalized_doc,
            public_key_b64=None,
            allow_db_fallback=False,
        )

        return JSONResponse(content={
            "success": True,
            "is_valid": result.get('is_valid', False),
            "message": "Подпись валидна" if result.get('is_valid') else "Подпись невалидна",
            "attrs": result.get('attrs', []),
            "checks": result.get('checks', {}),
        }, status_code=200)

    except Exception as ex:
        print(f"[ERROR] Ошибка в verify_document_unep: {ex}")
        return JSONResponse(content={
            "success": False,
            "is_valid": False,
            "message": str(ex),
            "attrs": [],
            "checks": {}
        }, status_code=500)

from datetime import datetime

class User(BaseModel):
    first_name:str
    last_name:str
    email:str
    is_email_verified:bool
    created_at: int
    public_key: str

@app.get("/api/user/info", 
         tags=["Пользователь"], 
         summary="Получение информации о пользователе",
         response_model=User
         )
async def get_user_info(token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
    """Получение информации о пользователе"""
    if not check_token_redis(db_redis, token, email):
        return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

    try:
        user = service.User(email, db, db_redis, flag_pg=True)
        content = user.get_all_info()
        return User(**content)

    except Exception as ex:
        print("[ERROR] Ошибка при получении информации о пользователе: ", ex)
        return JSONResponse(content={'status': service.GENERAL_ERROR_STATUS, "message": "Error fetching user info"}, status_code=500)

class UserUpdate(BaseModel):
    first_name:str
    last_name:str
    new_password:str

@app.post("/api/user/info/update", 
          tags=["Пользователь"], 
          summary="Обновление информации о пользователе"
          )
async def update_user_info(user_update: UserUpdate, token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
   """Обновление информации о пользователе"""
   if not check_token_redis(db_redis, token, email):
        return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

   try:
       user = service.User(email, db=db,flag_pg=True)
       flag = user.set_name(user_update.first_name, user_update.last_name)
       if flag:
           content = {'status': service.SUCCESS_STATUS,
                      'message': 'Информация успешно обновлена!'}
       else:
           content = {'status': service.GENERAL_ERROR_STATUS,
                      'message': 'Ошибка при обновлении информации'}
       return JSONResponse(content=content)

   except Exception as ex:
       print("[ERROR] Ошибка при обновлении информации о пользователе: ", ex)
       return JSONResponse(content={'status': service.GENERAL_ERROR_STATUS, "message": "Error updating user info"}, status_code=500)


class DocumentToSend(BaseModel):
    document_id:int = Field(..., description="ID документа для отправки", json_schema_extra={"example": 1})
    email_to_send:str = Field(..., description="Email получателя", json_schema_extra={"example": "recipient@example.com"})


@app.post("/api/document/send",
          tags=["Документы"], 
          summary="Отправка документа на подпись стороннему сервису")
async def send_document_to_external_service(send_info: DocumentToSend, token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
    """Отправка документа между пользователями"""
    if not check_token_redis(db_redis, token, email):
        return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

    try:
        if db.get_user_by_email(send_info.email_to_send) is None:
           return JSONResponse(content={'status': service.GENERAL_ERROR_STATUS, "message": "Email not found"}, status_code=404)
        else:
            document = db.get_document_by_id(send_info.document_id) 
            db.insert_doc(document['title'], document['hash'], document['created_at'], document['base64'], send_info.email_to_send)

    except Exception as ex:
        print(f"[ERROR] Ошибка при отправке документа: {ex}")
        return JSONResponse(content={'status': service.GENERAL_ERROR_STATUS, "message": "Error send document"}, status_code=500)

       
@app.get("/api/user/keys/generate",
         tags=["Пользователь"],
         summary="Генерация пары ключей для пользователя"
         )
async def generate_keys_for_user(token: Optional[str] = Header(None), email: Optional[str] = Header(None)):
    """Генерация пары ключей"""
    if not check_token_redis(db_redis, token, email):
        return JSONResponse(content={'status': service.INVALID_CREDENTIALS_STATUS, "message": "Invalid token"}, status_code=401)

    try:
        sign = SignatureUNEP(email, db)
        generated_keys = sign.generate_user_keys()
        if generated_keys is None:
            return JSONResponse(content={'status': service.GENERAL_ERROR_STATUS, "message": "Keys already exist"}, status_code=400)
        else:
            public_key_b64, private_key_b64 = generated_keys
            db.insert_keys_by_email(email, public_key_b64, private_key_b64)

            return JSONResponse(content={
                'status': service.SUCCESS_STATUS,
                "message": "Keys generated successfully",
                "public_key": public_key_b64
            }, status_code=200)

    except Exception as ex:
        print(f"[ERROR] Ошибка при генерации ключей для пользователя: {ex}")
        return JSONResponse(content={'status': service.GENERAL_ERROR_STATUS, "message": "Error generating keys"}, status_code=500)


#Добавить такие API call запросы, что бы сторонний сервис (например 1c) мог взаимодействовать с API таким образом:
#-регистрировать нового пользователя 
#-сформировать и отправить документ в БД, что бы пользователь с личного ПК мог его подписать 
#-как только пользователь подписывает и нажимает кнопку, документ отправляется обратно на сторонний сервис
# проверка подписи документа


@app.post("/api/v1/register", tags=["API стороннего сервиса"], summary="Регистрация нового пользователя")
async def register_user_1c(user:newUser):
   pass


class DocumentSome(Paper):
   endpoint: str = Field(..., description="Адрес возврата подписанного документа ", json_schema_extra={"example": "http://api/1C/somebody"} ) 
   deadlite_at: int = Field(..., description="Крайний срок подписи документа документа (Unix timestamp в секундах)", json_schema_extra={"example": 1704067200})
   

@app.post("/api/v1/document/insert", tags=["API стороннего сервиса"], summary="ОТправка документа для подписания")
async def insert_doc_1c(document:DocumentSome):
   pass




class ResponseDoc(BaseModel):
    document: Paper = Field(..., description="Подписанный документ в формате Paper")
    signatureIMG: SignatureRequest = Field(..., description="Подпись документа") # Графическаая
    signatureUNEP: str = Field(..., description="Подпись документа в формате УНЭП") 
    public_key: str = Field(..., description="Публичный ключ")

import httpx
async def send_signed_doc(callback_url:str, data:ResponseDoc):
   """Отправляет подписаный пользователем пдокумент обратно на 1С"""
   pass



# Эндпоинт чисто запускает задачу на отправку документа на 1С
@app.post("/api/v1/webhook", tags=["API стороннего сервиса"], summary="Возврат подписанного документа на сторонний сервис")
async def return_doc_to_1c(
   callback_url:str,
   background_tasks: BackgroundTasks
):
    """Этот эндпоинт будет вызываться после подписания документа пользователем. Он принимает URL для обратного вызова (callback_url) и использует BackgroundTasks для отправки подписанного документа на указанный URL без блокировки основного потока."""
    if not callback_url.startswith("http"):
        return JSONResponse(content={"success": False, "message": "Invalid callback URL"}, status_code=400)

    signed_data = ResponseDoc( # тут должно быть получение данных подписи и документа из бд
        document=Paper(
            filename="signed_report.pdf",
            content_base64="JVBERi0xLjQKJ..." # Пример контента
        ),
        signatureIMG=SignatureRequest(),
        signatureUNEP="MEUCIQDT...",
        public_key="-----BEGIN PUBLIC KEY-----..."
    )
    background_tasks.add_task(send_signed_doc, callback_url, signed_data)
    return JSONResponse(content={"success": True, "message": "Signed document will be sent shortly"}, status_code=200)


class SignatureValidationRequest(BaseModel):
   base64:str = Field(..., description="Подпись документа в формате Base64" )
   email:str = Field(..., description="Email пользователя, который подписал документ" )
   document_id: int = Field(..., description="ID подписанного документа" )
   endpoint: str = Field(..., description="Адрес возврата ", json_schema_extra={"example": "http://api/1C/somebody"} )

class SignatureValidationResponse(BaseModel):
    is_valid: bool = Field(..., description="Результат проверки подписи", json_schema_extra={"example": True})
    message: str = Field(..., description="Описание результата проверки")


@app.get("/api/v1/sign-verification", tags=["API стороннего сервиса"], summary="Проверка валидности подписи УНЭП", response_model=SignatureValidationResponse)
async def check_valid_sign(sign:SignatureValidationRequest):
    try:
        signer = SignatureUNEP(sign.email, db)
        doc = db.get_document_by_id(sign.document_id)

        if not doc:
            return JSONResponse(content={"is_valid": False, "message": "Документ не найден"}, status_code=404)

        result = signer.verify_cms_container(
             cms_signature_bytes=base64.b64decode(_normalize_base64_payload(sign.base64)),
             signed_document=_normalize_base64_payload(doc['base64']),
               public_key_b64=None,
               allow_db_fallback=False,
        )

        return SignatureValidationResponse(
            is_valid=result.get('is_valid', False),
            message="Подпись валидна" if result.get('is_valid', False) else "Подпись невалидна"
        )
    except Exception as ex:
        print(f"[ERROR] Ошибка в check_valid_sign: {ex}")
        return JSONResponse(content={"is_valid": False, "message": str(ex)}, status_code=500)



  # uvicorn main:app --reload
if __name__ == "__main__":
  uvicorn.run("main:app", reload=True)
  # команда для запуска теперь->
  # python main.py