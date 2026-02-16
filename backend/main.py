from fastapi import FastAPI, Response
from starlette.responses import JSONResponse
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel
import time
from typing import List
from database import Database 


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
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

#print("хеш логина= " + str(hash('admin@gmail.com')))
#print("хеш пароля= " + str(hash('adminadmin')))

# статусы ответов :
# 0 - успешный вход
# 2 - логин или пароль не верные
# 3 - нет связи с бд
# 4 - иная ошибка



def chek_auth(c_login:str, c_password:str):
  """ошибки при использовании бд не обрабатываются, нужно исправить"""
  try:
    db.connect()

    global newToken 
    if db.check_user(c_login, c_password):
      timeToLogin = time.time()
      sumToData = c_login + c_password
      newToken = hash(str(timeToLogin) + sumToData)
      return {
        "status" : 0,
        "token": newToken,
        "message": "Успешно!"
      }
    else: return {
        "status" : 2,
        "message": "Не верный логин или пароль"
    }
  except Exception as exept:
    print(exept)
    return {
        "status" : 4,
        "message": exept
    }
  finally: 
    db.close()

  


class oldUser(BaseModel):
  mail: str
  password: str
  

@app.post("/api/auth")
async def chek_login(old_user: oldUser):
  try:
    content = chek_auth(old_user.mail, old_user.password)
    headers = {
      "Access-Control-Allow-Origin": "*"
    } 
  except Exception as exept:
    print("Ошибка непосредственно в роуте: "+ exept) 

  return JSONResponse(content=content, headers=headers)

class Paper(BaseModel):
  id:int
  title: str
  hash: str
  created_at: int          # Unix timestamp в секундах
  base64: str              # PDF в base64
  login:str

# Модель ответа
class PapersResponse(BaseModel):
  message: str             # строка вида "There are X papers"
  papers: List[Paper]


@app.get("/api/docs", response_model=PapersResponse)
async def get_docs(login:str | None = None):
  db.connect()
  if login == None:
    result = list(db.check_docs('admin@gmail.com'))
    print("Запрос без параметров")
  else: 
    result = list(db.check_docs(str(login)))
    print(login)


  
  db.close()
  print(f"result: {result}\n\n\n\n")
  total = len(result)
  message =f"There are {total} paperes"

  paper = Paper(
      id=result[0],
      title=result[1],
      hash=result[2],          # .strip() удалит лишние пробелы, если они есть
      created_at=result[3],
      base64=result[4],
      login=result[5]
  )
  # Оборачиваем в список (так как papers ожидает список документов)
  papers_list = [paper]
  
  return PapersResponse(message=message, papers=papers_list)








  # uvicorn main:app --reload
if __name__ == "__main__":
  uvicorn.run("main:app", reload=True)
  # команда для запуска теперь->
  # python main.py