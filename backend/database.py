import psycopg2
from config_db import user, host, password, db_name,port



class Database:
  """Класс для работой с базой данных postgresql"""

  def __init__(self):
    self.connection = None
    self.host = host
    self.user = user
    self.password = password
    self.dbname = db_name
    self.port = port

  def connect(self):
    """Установление соединения с бд"""
    try:
      self.connection = psycopg2.connect(
        host=self.host,
        user=self.user,
        password=self.password,
        dbname=self.dbname,
        port=self.port
      )
      with self.connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        print(f"Server version: {cursor.fetchone()}")

      print("[INFO] Connection to PostgreSQL established")
      return self.connection
    except Exception as ex:
      print("[ERROR] Error connecting to database:", ex)
      



  def close(self):
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
              );
          """)
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
        print("[INFO] Data was successfully inserted")



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