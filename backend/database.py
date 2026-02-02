import psycopg2
from config_db import user, host, password, db_name,port







def createTableUsersSimple(connection): 
  """тестовое создание таблицы, нужно оптимизировать"""
  with connection.cursor() as cursor:
    cursor.execute(
      """CREATE TABLE users(
      id serial PRIMARY KEY,
      login varchar(50) NOT NULL,
      password varchar(50) NOT NULL);""")
    connection.commit()
    print(f"[INFO] Table create successfully")


def insertDataInUsers(connection, login:str, password:str):
  """Добавление данных в таблицу users, защита отсутствует"""
  with connection.cursor() as cursor:
    cursor.execute(
      f"""INSERT INTO users (login, password) VALUES
      ('{login}', '{password}')""")
    connection.commit()
    print(f"[INFO] Data was successfully inserted")

def checkDataInUsers(connection, login:str, password:str)-> bool:
  """Проверка логина и пароля, защита отсутствует"""
  try:
    with connection.cursor() as cursor:
      cursor.execute(
        f"""SELECT password FROM users WHERE login ='{login}';""")
      response = cursor.fetchone()
      if response[0] == password:
        #print(response)
        print("[INFO] checkDataInUsers seccessfully")
        return True
    return False
  except Exception as ex:
    print("[ERROR] checkDataInUsers error: ", ex)

def connectToDB():
  try:
    connection = psycopg2.connect(
      host=host,
      user=user,
      password=password,
      dbname=db_name,
      port=port
    )
    with connection.cursor() as cursor:
      cursor.execute("" \
      "SELECT version();")
      print(f"Server version: {cursor.fetchone()}")
    return connection
    #createTableUsersSimple(connection)
    #print(checkDataInUsers(connection=connection, login='admin@gmail.com', password='adminadmin'))
    

  except Exception as ex:
    print("[ERROR]: Error worker database postgresql", ex)

def closeConnect(connection):
  connection.close()
  print("[INFO] Postgresql connection closed")
