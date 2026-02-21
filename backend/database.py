import psycopg2
import psycopg2.extras
from config_db import user, host, password, db_name,port


class Database:
  """Класс для работой с базой данных postgresql"""

  def __init__(self):
    """Установление соединения с бд"""
    try:
      self.connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=db_name,
        port=port )
      with self.connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        print(f"Server version: {cursor.fetchone()}")

      print("[INFO] Connection to PostgreSQL established")
      #return self.connection
    except Exception as ex:
      print("[ERROR] Error connecting to database:", ex)
      

  def __del__(self):
    """Закрывает соединение с базой данных"""
    if self.connection:
      self.connection.close()
      print("[INFO] PostgreSQL connection closed")



  def _create_table_users_simple(self):
      """
      Приватный метод: создаёт таблицу users.
      (тестовое создание таблицы, нуждается в оптимизации)
      """
      if not self.connection:
          raise ConnectionError("No active database connection")
      with self.connection.cursor() as cursor:
          cursor.execute("""
              CREATE TABLE users(
                  id serial PRIMARY KEY,
                  login varchar(50) NOT NULL,
                  password varchar(50) NOT NULL
              );""")
          self.connection.commit()
          print("[INFO] Table created successfully")



  def insert_user(self, login: str, password: str):
    """
    Публичный метод: добавляет пользователя в таблицу users.
    (защита от SQL-инъекций отсутствует)
    """
    if not self.connection:
        raise ConnectionError("No active database connection")
    with self.connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO users (login, password) VALUES ('{login}', '{password}');"
        )
        self.connection.commit()
        print(f"[INFO] User {login} was successfully inserted")



  def check_user(self, login: str, password: str) -> bool:
    """
    Публичный метод: проверяет существование пользователя с указанным паролем.
    (защита от SQL-инъекций отсутствует)
    """
    if not self.connection:
        raise ConnectionError("No active database connection")
    try:
        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT password FROM users WHERE login = '{login}';")
            result = cursor.fetchone()
            if result and result[0] == password:
                print("[INFO] User checked successfully")
                return True
        return False
    except Exception as ex:
        print("[ERROR] Error in check_user:", ex)
        return False
    
  

  def check_docs(self, login:str) -> tuple:
    """
    Публичный метод: вытаскивает все документу загруженные или отправленные конкретному пользователю
    """
    if not self.connection:
      raise ConnectionError("No Activate database connection")
    try:
      with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor: # нужно в дальнейшем добавить категории документов, подписан, необходимо подписать 
        cursor.execute(f""" 
            SELECT 
                d.id,
                d.title,
                d.hash,
                d.created_at,
                d.base64,
                u.login
            FROM documents d
            JOIN users u ON d.user_id = u.id
            WHERE u.login = '{login}'          -- логин пользователя
            ORDER BY d.created_at DESC;
                       """) 
        results = cursor.fetchall()
        return results
      
    except Exception as ex:
      print("[ERROR] Error in check_docs:", ex)
      


  def insert_doc(self, title:str, hash:str, created_at:int, base64:str, login:int):
    """
    Публичный метод: добавление документа в бд
    (Защита от SQL инъекций отсутствует)
    """
    if not self.connection:
      raise ConnectionError("No Activate database connection")
    try:
      print(f'[INFO]\ntitle:{title}\nhash:{hash}\ncreated_at:{created_at}\nbase64:{base64:64}\nlogin:{login}')
      with self.connection.cursor() as cursor:
        cursor.execute(f"""
          INSERT INTO documents (title, hash, created_at, base64, user_id)
          VALUES ('{title}', '{hash}','{created_at}', '{base64}', (SELECT id FROM users WHERE login = '{login}'));
                       """) 
        self.connection.commit()
        print(f"[INFO] Document {title} was successfully inserted")
      return True
    except Exception as ex:
      print("[ERROR] Error in insert_doc:", ex)
      return False





  def delet_doc(self, id: int):
    """
    Публичный метод: удаляет документт по уникальному id
    (Защита от SQL инъекций отсутствует)
    """
    if not self.connection:
      raise ConnectionError("No Activate database connection")
    try:
      with self.connection.cursor() as cursor:
        cursor.execute(f"""
            DELETE FROM documents WHERE id = '{id}';
                       """)
        self.connection.commit() 
        print(f"[INFO] Document id: {id}, deleted success")

    except Exception as ex:
      print("[ERROR] Error in delet_doc:", ex)
