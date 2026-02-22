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



  def insert_user(self, login: str, password: str) -> bool:
    """
    Публичный метод: добавляет пользователя в таблицу users.
    Использует параметризованные запросы для защиты от SQL-инъекций.
    """
    if not self.connection:
      raise ConnectionError("No active database connection")
    try:
      with self.connection.cursor() as cursor:
        # Используем %s плейсхолдеры для параметризованного запроса
        cursor.execute(
            "INSERT INTO users (login, password) VALUES (%s, %s);",
            (login, password)
        )
        self.connection.commit()
        print(f"[INFO] User {login} was successfully inserted")
        return True
    except Exception as ex:
      print('[ERROR] Error in the insert_user ', ex)




  def check_user(self, login: str, password: str) -> bool | int:
    """
    Публичный метод: проверяет существование пользователя с указанным паролем.
    Использует параметризованные запросы для защиты от SQL-инъекций.
    """
    if not self.connection:
        raise ConnectionError("No active database connection")
    try:
      with self.connection.cursor() as cursor:
        # Параметризованный запрос - безопасен от SQL-инъекций
        cursor.execute("SELECT password FROM users WHERE login = %s;", (login,))
        result = cursor.fetchone()
       
        if result and result[0] == password:
          print("[INFO] User checked successfully")
          return True 
      
      return False 
    except Exception as ex:
      print("[ERROR] Error in the check_user:", ex)
    
    return 3 # статус код ошибки с базой данных 
    
  

  def check_docs(self, login:str) -> list:
    """
    Публичный метод: вытаскивает все документы загруженные или отправленные конкретному пользователю.
    Использует параметризованные запросы для защиты от SQL-инъекций.
    """
    if not self.connection:
      raise ConnectionError("No Activate database connection")
    try:
      # RealDictCursor возвращает результаты в виде словарей
      with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        # Параметризованный запрос с плейсхолдером %s
        cursor.execute(""" 
            SELECT 
                d.id,
                d.title,
                d.hash,
                d.created_at,
                d.base64,
                u.login
            FROM documents d
            JOIN users u ON d.user_id = u.id
            WHERE u.login = %s
            ORDER BY d.created_at DESC;
        """, (login,)) 
        results = cursor.fetchall()
        return results
      
    except Exception as ex:
      print("[ERROR] Error in the check_docs:", ex)
    
    return []
      


  def insert_doc(self, title:str, hash:str, created_at:int, base64:str, login:str):
    """
    Публичный метод: добавление документа в базу данных.
    Использует параметризованные запросы для защиты от SQL-инъекций.
    
    Args:
        title: Название документа
        hash: SHA-256 хеш документа
        created_at: Unix timestamp создания
        base64: Содержимое PDF в base64
        login: Email пользователя
    """
    if not self.connection:
      raise ConnectionError("No Activate database connection")
    try:
      print(f'[INFO]\ntitle:{title}\nhash:{hash}\ncreated_at:{created_at}\nbase64:{base64[:64]}...\nlogin:{login}')
      with self.connection.cursor() as cursor:
        # Параметризованный запрос с подзапросом для получения user_id
        cursor.execute("""
          INSERT INTO documents (title, hash, created_at, base64, user_id)
          VALUES (%s, %s, %s, %s, (SELECT id FROM users WHERE login = %s));
        """, (title, hash, created_at, base64, login)) 
        self.connection.commit()
        print(f"[INFO] Document {title} was successfully inserted")
        return True
    except Exception as ex:
      print("[ERROR] Error in insert_doc:", ex)
    
    return False



  def delet_doc(self, id: int) -> bool:
    """
    Публичный метод: удаляет документ по уникальному id из БД.
    Использует параметризованные запросы для защиты от SQL-инъекций.
    
    Args:
        id: Уникальный идентификатор документа
    """
    if not self.connection:
      raise ConnectionError("No Activate database connection")
    try:
      with self.connection.cursor() as cursor:
        # Параметризованный запрос - безопасен от SQL-инъекций
        cursor.execute("DELETE FROM documents WHERE id = %s;", (id,))
        self.connection.commit() 
        print(f"[INFO] Document id: {id}, deleted success")
        return True
    except Exception as ex:
      print("[ERROR] Error in delet_doc:", ex)
    
    return False


  def get_document_by_id(self, doc_id: int) -> dict | None:
    """
    Публичный метод: получает документ по его уникальному ID.
    Используется для получения документа перед подписанием.
    
    Args:
        doc_id: Уникальный идентификатор документа
        
    Returns:
        Словарь с данными документа или None, если документ не найден
    """
    if not self.connection:
      raise ConnectionError("No active database connection")
    try:
      with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("""
            SELECT 
                d.id,
                d.title,
                d.hash,
                d.created_at,
                d.base64,
                u.login
            FROM documents d
            JOIN users u ON d.user_id = u.id
            WHERE d.id = %s;
        """, (doc_id,))
        result = cursor.fetchone()
        
        if result:
          print(f"[INFO] Document id: {doc_id} retrieved successfully")
          return dict(result)
        else:
          print(f"[WARNING] Document id: {doc_id} not found")
          return None
          
    except Exception as ex:
      print(f"[ERROR] Error in get_document_by_id: {ex}")
      return None


  def insert_signed_document(self, title: str, hash: str, created_at: int, 
                             base64: str, login: str, original_doc_id: int = None,
                             signer: str = None, signature_data: dict = None) -> int | None:
    """
    Публичный метод: добавляет подписанный документ в базу данных.
    Сохраняет связь с оригинальным документом и информацию о подписи.
    
    Args:
        title: Название подписанного документа
        hash: SHA-256 хеш подписанного документа
        created_at: Unix timestamp создания
        base64: Содержимое подписанного PDF в base64
        login: Email пользователя (владельца документа)
        original_doc_id: ID оригинального документа (опционально)
        signer: Email подписавшего пользователя (опционально)
        signature_data: Дополнительные данные о подписи (координаты, размер и т.д.)
        
    Returns:
        ID нового документа или None при ошибке
    """
    if not self.connection:
      raise ConnectionError("No active database connection")
    try:
      print(f'[INFO] Inserting signed document: {title}')
      with self.connection.cursor() as cursor:
        # Вставляем подписанный документ
        cursor.execute("""
          INSERT INTO documents (title, hash, created_at, base64, user_id)
          VALUES (%s, %s, %s, %s, (SELECT id FROM users WHERE login = %s))
          RETURNING id;
        """, (title, hash, created_at, base64, login))
        
        # Получаем ID только что вставленного документа
        new_doc_id = cursor.fetchone()[0]
        
        # Если есть данные о подписи, сохраняем их в отдельную таблицу (если она существует)
        if signature_data and signer:
          try:
            cursor.execute("""
              INSERT INTO document_signatures 
              (document_id, signer_id, signature_image_base64, page_number, 
               x_position, y_position, width, height, signed_at)
              VALUES (
                %s, 
                (SELECT id FROM users WHERE login = %s),
                %s, %s, %s, %s, %s, %s, NOW()
              );
            """, (
              new_doc_id,
              signer,
              signature_data.get('signature_base64', ''),
              signature_data.get('page_number', 0),
              signature_data.get('x', 0),
              signature_data.get('y', 0),
              signature_data.get('width', 0),
              signature_data.get('height', 0)
            ))
            print(f"[INFO] Signature metadata saved for document {new_doc_id}")
          except Exception as sig_ex:
            # Если таблица подписей не существует, просто игнорируем
            print(f"[WARNING] Could not save signature metadata: {sig_ex}")
        
        self.connection.commit()
        print(f"[INFO] Signed document {title} was successfully inserted with ID: {new_doc_id}")
        return new_doc_id
        
    except Exception as ex:
      print(f"[ERROR] Error in insert_signed_document: {ex}")
      return None
