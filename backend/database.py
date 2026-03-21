import psycopg2
from psycopg2 import errorcodes
import psycopg2.extras
from config_db import user, host, password, db_name,port
from hashlib import sha256
from time import time


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
      
      # Включение автокоммита
      self.connection.autocommit = True
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


  def insert_user(self, login: str, password: str, name:dict | None = None) -> bool:
    """
    Публичный метод: добавляет пользователя в таблицу users.
    Использует параметризованные запросы для защиты от SQL-инъекций.
    Args:
    name: dict= {'firstName': 'name', 'lastName': 'name'} | None
    """
    password_hash = sha256(password.encode()).hexdigest()

    if not self.connection:
      raise ConnectionError("No active database connection")
    try:
      with self.connection.cursor() as cursor:
        # Используем %s плейсхолдеры для параметризованного запроса
        if name is None:
          cursor.execute(
              "INSERT INTO users (email, password_hash) VALUES (%s, %s);",
              (login, password_hash)
          )
        # тут нужна проверка и валидация параметра name более тщательная 
        elif 'firstName' in name and 'lastName' in name: 
          cursor.execute(
              "INSERT INTO users (email, password_hash, first_name, last_name) VALUES (%s, %s, %s, %s);",
                (login, password_hash, name['firstName'], name['lastName'])
          )
        else: 
          print("[INFO] Не валидная структура name", name)
          return False
        self.connection.commit()
        print(f"[INFO] User {login} was successfully inserted")
        
        return True
      
    except psycopg2.Error as ex:
      if ex.pgcode == errorcodes.UNIQUE_VIOLATION:
        print("[INFO] Email is not originality", ex)
        # нужно следать что то польше, чем строка в консоль, например отправить на API сообщение, о том что это не ошибка бд, а именно проблема уникальности
      else:
        print('[ERROR] Error in the insert_user ', ex)
      
      return False


  def check_user(self, email: str, password: str) -> int:
    """
    Публичный метод: проверяет существование пользователя с указанным паролем.
    Использует параметризованные запросы для защиты от SQL-инъекций.

      Returns:
      0 - успешный вход
      2 - логин или пароль не верные или совпадают
      3 - нет связи или ошибка с бд
 
    """
    SUCCESS_STATUS = 0              # 0 - успешный вход
    INVALID_CREDENTIALS_STATUS = 2  # 2 - логин или пароль не верные или совпадают
    DB_CONNECTION_ERROR_STATUS = 3  # 3 - нет связи или ошибка с бд

    password_hash = sha256(password.encode()).hexdigest()

    if not self.connection:
      return DB_CONNECTION_ERROR_STATUS
        
    try:
      with self.connection.cursor() as cursor:
        # Параметризованный запрос - безопасен от SQL-инъекций
        cursor.execute("SELECT password_hash FROM users WHERE email = %s;", (email,))
        result = cursor.fetchone()
       
        if result and result[0] == password_hash:
          print("[INFO] User checked successfully")
          return SUCCESS_STATUS
      
      return INVALID_CREDENTIALS_STATUS
    except Exception as ex:
      print("[ERROR] Error in the check_user:", ex)
      return ex
    

  def get_all_list_docs(self, email:str) -> list:
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
                d.base64,
                d.created_at,
                u.email
            FROM documents d
            JOIN users u ON d.owner_id = u.id
            WHERE u.email = %s
            ORDER BY d.created_at DESC;
        """, (email,)) 
        results = cursor.fetchall()
        return results
      
    except Exception as ex:
      print("[ERROR] Error in the check_docs:", ex)
    return []
    

  def insert_doc(self, title:str, hash:str, created_at:int, base64:str, email:str):
    """
    Публичный метод: добавление документа в базу данных.
    Использует параметризованные запросы для защиты от SQL-инъекций.
    
    Args:
        title: Название документа
        hash: SHA-256 хеш документа
        created_at: Unix timestamp создания
        base64: Содержимое PDF в base64
        email: Email пользователя
    """
    if not self.connection:
      raise ConnectionError("No Activate database connection")
    try:
      print(f'[INFO]\ntitle:{title}\nhash:{hash}\ncreated_at:{created_at}\nbase64:{base64[:64]}...\nlogin:{email}')
      with self.connection.cursor() as cursor:
        # Параметризованный запрос с подзапросом для получения user_id
        cursor.execute("""
          INSERT INTO documents (title, hash, base64, owner_id)
          VALUES (%s, %s, %s, (SELECT id FROM users WHERE email = %s));
        """, (title, hash, base64, email)) 
        self.connection.commit()
        print(f"[INFO] Document {title} was successfully inserted")
        return True
    except Exception as ex:
      print("[ERROR] Error in insert_doc:", ex)
    
    return False

  def delet_document_by_id(self, id: int) -> bool:
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
                u.email
            FROM documents d
            JOIN users u ON d.owner_id = u.id
            WHERE d.id = %s;
        """, (doc_id,))
        result = cursor.fetchone()
        
        if result:
          print(f"[INFO] Document id: {doc_id} retrieved successfully")
          return dict(result)
        else:
          print(f"[ERROR] Document id: {doc_id} not found")
          return None
          
    except Exception as ex:
      print(f"[ERROR] Error in get_document_by_id: {ex}")
      return None


  def __create_void_signature_rout(self, document_id, email, signature_note:str = None, deadline:int = None):
    """Создание пустой задачи для единовременной подписи
      Если клиент хочет просто зайти и подписать сам свой документ,
      что бы не нагружать его лишним созданием задачи и не ломать триггеры в бд"""
    result = None
    if deadline is None:
      deadline = int(time()) + 100

    if not self.connection:
      raise ConnectionError("No active database connection")
    try:
      with self.connection.cursor() as cursor:
        cursor.execute("""
          INSERT INTO signature_routes (document_id, required_signer_id, order_index, signature_note, deadline_at)
          VALUES (%s, (SELECT id FROM users WHERE email = %s), %s, %s, %s)
          RETURNING id;
        """, (document_id, email, '1', signature_note, deadline))
        result = cursor.fetchone[0]
        self.connection.commit()
      return result
    except Exception as ex:
      print("[ERROR] Error in __create_void_signature_rout ", ex)
        


  def insert_signed_document(self, title: str, hash: str, created_at: int, 
                             base64: str, email: str, original_doc_id: int = None,
                             signer: str = None, signature_data: dict = None) -> int | None:
    """
    Публичный метод: добавляет подписанный документ в базу данных.
    Сохраняет связь с оригинальным документом и информацию о подписи.
    
    Args:
        title: Название подписанного документа
        hash: SHA-256 хеш подписанного документа
        created_at: Unix timestamp создания
        base64: Содержимое подписанного PDF в base64
        email: Email пользователя (владельца документа)
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
          INSERT INTO documents (title, hash, base64, owner_id, created_at)
          VALUES (%s, %s, %s,(SELECT id FROM users WHERE email = %s), %s)
          RETURNING id;
        """, (title, hash, base64, email, created_at))
        
        # Получаем ID только что вставленного документа
        new_doc_id = cursor.fetchone()[0]
        # Получаем ID тлько что сделанной задачи, что бы триггеры не сломались
        #signature_route_id = self.__create_void_signature_rout(new_doc_id,email) # Идея толковая, но почему то в БД создается подпись, но не привязанная к маршруту
        signature_route_id = None
        # Если есть данные о подписи, сохраняем их в отдельную таблицу (если она существует)
        if signature_data and signer:
          try:
            cursor.execute("""
              INSERT INTO document_signatures 
              (document_id, signer_id, signature_route_id, signature_image_base64, page_number, 
               x_position, y_position, width, height)
              VALUES (
                %s, 
                (SELECT id FROM users WHERE email = %s),
                %s, %s, %s, %s, %s, %s, %s );
            """, (
              new_doc_id,
              signer,
              signature_route_id,
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


  def get_user_by_email(self, email: str) -> dict | None:
    """
    Публичный метод: получает данные человека по его почте.
    
    Args:
        email: Уникальный идентификатор пользователя
        
    Returns:
        Словарь с данными пользователя или None, если не найден
    """
    if not self.connection:
      raise ConnectionError("No active database connection")
    try:
      with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("""
            SELECT 
                u.id,
                u.first_name,
                u.last_name,
                u.is_email_verified,
                u.created_at
            FROM users u
            WHERE u.email = %s;
        """, (email,))
        result = cursor.fetchone()
        
        if result:
          print(f"[INFO] User: {email} retrieved successfully")
          return dict(result)
        else:
          print(f"[ERROR] User: {email} not found")
          return None
          
    except Exception as ex:
      print(f"[ERROR] Error in get_user_by_email: {ex}")
      return None


  def change_userName_by_id (self, id, new_first_name:str, new_last_name:str): 
    
    if not self.connection:
      raise ConnectionError("No active database connection")
    try:
      with self.connection.cursor() as cursor:
        cursor.execute("""
            UPDATE users 
            SET 
              first_name = %s, 
              last_name = %s,
              updated_at = EXTRACT(EPOCH FROM NOW())::BIGINT
            WHERE id = %s;
        """, (new_first_name, new_last_name, id))
        
      print(f'[INFO] User name {new_first_name} successfulle change')
          
    except Exception as ex:
      print(f"[ERROR] Error in change_userName_by_id: {ex}")
      return None
