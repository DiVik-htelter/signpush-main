from fastapi import FastAPI, Response, Query, Path
from starlette.responses import JSONResponse
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel, Field
import time
from typing import List, Optional
from database import Database
from pdf_signer import PdfSigner

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SignPush API",
    description="API для управления документами и электронной подписи PDF файлов",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
db = Database()

# Разрешенные источники
origins = [
    "http://localhost:3000",
    "http://localhost:8000"
]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Список источников
    allow_credentials=True,  # Разрешить Cookies
    allow_methods=["*"],  # Разрешить все методы (GET, POST, etc.)
    allow_headers=["*"],  # Разрешить все заголовки
)
newToken = None

# статусы ответов :
# 0 - успешный вход
# 2 - логин или пароль не верные
# 3 - нет связи с бд
# 4 - иная ошибка

SUCCESS_STATUS = 0
INVALID_CREDENTIALS_STATUS = 2
DB_CONNECTION_ERROR_STATUS = 3
GENERAL_ERROR_STATUS = 4


def chek_auth(c_login:str, c_password:str):
  """ошибки при использовании бд не обрабатываются, нужно исправить"""
  try:

    global newToken 
    if db.check_user(c_login, c_password):
      timeToLogin = time.time()
      sumToData = c_login + c_password
      newToken = hash(str(timeToLogin) + sumToData)
      return {
        "status" : SUCCESS_STATUS,
        "token": newToken,
        "message": "Успешно!"
      }
    else: return {
        "status" : INVALID_CREDENTIALS_STATUS,
        "message": "Не верный логин или пароль"
    }
  except Exception as exept:
    print(exept)
    return {
        "status" : GENERAL_ERROR_STATUS,
        "message": exept
    }



class oldUser(BaseModel):
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
async def chek_login(old_user: oldUser):
  """
  Проверка учетных данных и выдача токена аутентификации
  
  **Коды статуса ответа:**
  - 0: Успешная аутентификация
  - 2: Неверный логин или пароль
  - 4: Внутренняя ошибка сервера
  """
  try:
    content = chek_auth(old_user.mail, old_user.password)
    headers = {
      "Access-Control-Allow-Origin": "*"
    } 
  except Exception as exept:
    print("Ошибка непосредственно в роуте: "+ exept) 

  return JSONResponse(content=content, headers=headers)

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
  created_at: int = Field(
      ..., 
      description="Время создания документа (Unix timestamp в секундах)",
      json_schema_extra={"example": 1704067200}
  )
  base64: str = Field(
      ..., 
      description="Содержимое документа в формате Base64",
      json_schema_extra={"example": "JVBERi0xLjQKJeHo8OXo8eHo8eHo..."}
  )
  login: str = Field(
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
  papers: List[Paper] = Field(
      ..., 
      description="Список документов пользователя"
  )


@app.get(
    "/api/docs", 
    response_model=PapersResponse,
    summary="Получение списка документов",
    tags=["Документы"],
    description="Получить список всех документов пользователя по его email адресу. Если параметр не указан, используется 'admin@gmail.com' по умолчанию"
)
async def get_docs(
    login: str | None = Query(
        None, 
        description="Email адрес пользователя для получения его документов",
        json_schema_extra={"example": "admin@gmail.com"}
    )
):
  """Получение списка документов по логину"""
  if login is None:
    login = 'admin@gmail.com'
    print("Запрос без параметров")
  
  result = db.check_docs(str(login))
  total = len(result)
  message =f"There are {total} paperes"

  papers_list = [Paper(**doc) for doc in result]
  
  return PapersResponse(message=message, papers=papers_list)



class InsertDocResponse(BaseModel):
  success: bool = Field(
      ..., 
      description="Флаг успешного добавления документа",
      json_schema_extra={"example": True}
  )


@app.post(
    "/api/insertDocs",
    response_model=InsertDocResponse,
    summary="Загружка нового документа",
    tags=["Документы"],
    description="Добавить новый PDF документ в систему. Документ должен быть предварительно закодирован в Base64 формат"
)
async def insert_docs(paper: Paper):
  """Добавление нового документа в базу данных"""
  
  try:
    flag = db.insert_doc(paper.title, paper.hash, paper.created_at, paper.base64, paper.login)
    headers = {
      "Access-Control-Allow-Origin": "*"
    } 
    content = { 
      "success": flag
    }
  except Exception as exept:
    print("Ошибка непосредственно в роуте добавления документа: ", exept) 

  return JSONResponse(content=content, headers=headers)

class DeleteDocResponse(BaseModel):
  success: bool = Field(
      ..., 
      description="Флаг успешного удаления документа",
      json_schema_extra={"example": True}
  )


@app.delete(
    "/api/docs/{doc_id}",
    response_model=DeleteDocResponse,
    summary="Удаление документа",
    tags=["Документы"],
    description="Удалить документ по его ID из системы. После удаления документ больше не будет доступен"
)
async def doc_delete(
    doc_id: int = Path(
        ..., 
        description="Уникальный идентификатор документа для удаления",
        json_schema_extra={"example": 123},
        gt=0
    )
):
  """Удаление документа по ID"""
  flag = False
  try:
    flag = db.delet_doc(doc_id) # id документа, который автоматически выдается в базе данных 
  except Exception as ex:
    print('Ошибка при удалениии документа из БД: ', ex)
  
  content = {'success': flag}
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
    "/api/sign-document",
    response_model=SignDocumentResponse,
    summary="Подписание PDF документа визуальной подписью",
    tags=["Подписание документов"],
    description="Электронная подпись PDF документа с визуальным отображением подписи на странице. Процесс: 1. Получение документа из БД 2. Встраивание подписи в PDF 3. Вычисление нового хеша 4. Сохранение подписанного документа"
)
async def sign_document(request: SignatureRequest):
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
        print(f"\n[API] Received signature request for document ID: {request.document_id}")
        
        # Валидация параметров подписи
        valid, error_msg = PdfSigner.validate_signature_params(
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
        
        print(f"[API] Original document retrieved: {doc['title']}")
        
        # Встраиваем подпись в PDF
        signer = PdfSigner()
        signed_pdf, success = signer.add_signature_to_pdf(
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
        import hashlib
        signed_pdf_clean = signed_pdf.split('base64,')[-1] if 'base64,' in signed_pdf else signed_pdf
        new_hash = hashlib.sha256(signed_pdf_clean.encode()).hexdigest()
        
        print(f"[API] New hash calculated: {new_hash[:16]}...")
        
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
            created_at=int(time.time()),
            base64=signed_pdf,
            login=request.login,
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


  # uvicorn main:app --reload
if __name__ == "__main__":
  uvicorn.run("main:app", reload=True)
  # команда для запуска теперь->
  # python main.py