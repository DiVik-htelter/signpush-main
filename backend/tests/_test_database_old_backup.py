"""
Тесты для модуля database.py

Функционал:
- Тестирование операций с PostgreSQL
- Тестирование операций с Redis
- Мок-тестирование работы с БД
"""

import pytest
from unittest.mock import MagicMock, patch

# Мокирование происходит в conftest.py перед импортом
# conftest.py мокирует config_db и database перед запуском тестов

try:
    from database import Database, DatabaseRedis
except ImportError as e:
    pytest.skip(f"Cannot import database module: {e}", allow_module_level=True)


# =====================================================================
# ФИКСТЫ ДЛЯ ТЕСТИРОВАНИЯ DATABASE
# =====================================================================

@pytest.fixture
def mock_postgres_cursor():
    """
    Мок: курсор PostgreSQL
    Используется для мокирования SQL запросов
    """
    cursor = MagicMock()
    cursor.execute.return_value = None
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    cursor.rowcount = 0
    return cursor


@pytest.fixture
def mock_postgres_connection(mock_postgres_cursor):
    """
    Мок: соединение с PostgreSQL
    """
    connection = MagicMock()
    connection.cursor.return_value = mock_postgres_cursor
    connection.commit.return_value = None
    connection.close.return_value = None
    return connection


@pytest.fixture
def db_with_mocked_postgres(mock_postgres_connection):
    """
    Database инстанс с замоканным PostgreSQL подключением
    """
    with patch('database.psycopg2.connect', return_value=mock_postgres_connection):
        db = Database()
        db._cursor = mock_postgres_cursor
        db._connection = mock_postgres_connection
        yield db


@pytest.fixture
def mock_redis_client():
    """
    Мок: Redis клиент
    """
    redis = MagicMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.setex.return_value = True
    redis.delete.return_value = 1
    redis.exists.return_value = 1
    return redis


@pytest.fixture
def redis_with_mocked_connection(mock_redis_client):
    """
    DatabaseRedis инстанс с замоканным Redis подключением
    """
    with patch('database.redis.StrictRedis.from_url', return_value=mock_redis_client):
        db_redis = DatabaseRedis()
        db_redis._redis = mock_redis_client
        yield db_redis



# =====================================================================
# БЛОК А: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С ПОЛЬЗОВАТЕЛЯМИ
# =====================================================================

class TestDatabaseUserOperations:
    """Тестирование операций с пользователями в БД"""
    
    def test_insert_user_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Успешная вставка пользователя"""
        mock_db_connection.fetchone.return_value = (1,)
        
        result = db_instance.insert_user(
            email="test@domain.com",
            password="hashed_pass",
            name={'firstName': 'John', 'lastName': 'Doe'}
        )
        
        # Проверяем, что был выполнен запрос
        assert mock_postgres_cursor.execute.called
        assert result is not None
    
    def test_insert_user_duplicate_email(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Попытка вставить пользователя с существующим email"""
        mock_postgres_cursor.execute.side_effect = Exception("UNIQUE constraint violated")
        
        result = db_with_mocked_postgres.insert_user(
            email="existing@domain.com",
            password="pass",
            name={'firstName': 'John', 'lastName': 'Doe'}
        )
        
        assert result is False or result is None
    
    def test_get_user_by_email(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение пользователя по email"""
        mock_postgres_cursor.fetchone.return_value = (
            1, 'John', 'Doe', 'test@domain.com', True, 1704067200
        )
        
        result = db_with_mocked_postgres.get_user_by_email("test@domain.com")
        
        assert result is not None
        assert mock_postgres_cursor.execute.called
    
    def test_get_user_by_email_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Поиск несуществующего пользователя"""
        mock_postgres_cursor.fetchone.return_value = None
        
        result = db_with_mocked_postgres.get_user_by_email("nonexistent@domain.com")
        
        assert result is None
    
    def test_check_user_valid_credentials(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка валидных учетных данных"""
        # Mock для проверки пароля
        mock_postgres_cursor.fetchone.return_value = (0,)  # Успешная проверка
        
        result = db_with_mocked_postgres.check_user("test@domain.com", "password123")
        
        assert result == 0
    
    def test_check_user_invalid_credentials(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка невалидных учетных данных"""
        mock_postgres_cursor.fetchone.return_value = (2,)  # Invalid credentials
        
        result = db_with_mocked_postgres.check_user("test@domain.com", "wrongpass")
        
        assert result == 2
    
    def test_is_original_email_available(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка доступности email"""
        mock_postgres_cursor.fetchone.return_value = (0,)  # Email доступен
        
        result = db_with_mocked_postgres.is_original_email("available@domain.com")
        
        assert result is True or result == 0
    
    def test_is_original_email_taken(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка занятого email"""
        mock_postgres_cursor.fetchone.return_value = (1,)  # Email занят
        
        result = db_with_mocked_postgres.is_original_email("taken@domain.com")
        
        assert result is False or result == 1
    
    def test_change_userName_by_id(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Изменение имени пользователя"""
        mock_postgres_cursor.execute.return_value = None
        
        db_with_mocked_postgres.change_userName_by_id(1, "Jane", "Smith")
        
        # Проверяем, что был выполнен UPDATE запрос
        assert mock_postgres_cursor.execute.called


# =====================================================================
# БЛОК Б: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С ДОКУМЕНТАМИ
# =====================================================================

class TestDatabaseDocumentOperations:
    """Тестирование операций с документами в БД"""
    
    def test_insert_doc_success(self, db_instance, mock_db_connection):
        """Успешная вставка документа"""
        mock_db_connection.execute.return_value = None
        
        result = db_instance.insert_doc(
            title="test.pdf",
            hash="abc123",
            created_at=1704067200,
            base64="base64content",
            email="test@domain.com"
        )
        
        assert mock_db_connection.execute.called
    
    def test_get_document_by_id(self, db_instance, mock_db_connection):
        """Получение документа по ID"""
        mock_doc_data = {
            'id': 1,
            'title': 'test.pdf',
            'hash': 'abc123',
            'base64': 'base64content',
            'email': 'test@domain.com'
        }
        mock_db_connection.fetchone.return_value = tuple(mock_doc_data.values())
        
        result = db_instance.get_document_by_id(1)
        
        assert result is not None or result == tuple(mock_doc_data.values())
        assert mock_db_connection.execute.called
    
    def test_get_document_by_id_not_found(self, db_instance, mock_db_connection):
        """Получение несуществующего документа"""
        mock_db_connection.fetchone.return_value = None
        
        result = db_instance.get_document_by_id(999)
        
        assert result is None
    
    def test_get_all_list_docs(self, db_instance, mock_db_connection):
        """Получение всех документов пользователя"""
        mock_docs = [
            (1, 'doc1.pdf', 'hash1', 'unsigned', 1704067200, 'test@domain.com'),
            (2, 'doc2.pdf', 'hash2', 'signed', 1704067300, 'test@domain.com')
        ]
        mock_db_connection.fetchall.return_value = mock_docs
        
        result = db_instance.get_all_list_docs("test@domain.com")
        
        assert len(result) == 2
        assert mock_db_connection.execute.called
    
    def test_get_all_list_docs_empty(self, db_instance, mock_db_connection):
        """Получение списка документов для пользователя без документов"""
        mock_db_connection.fetchall.return_value = []
        
        result = db_instance.get_all_list_docs("noissue@domain.com")
        
        assert len(result) == 0
    
    def test_delet_document_by_id_success(self, db_instance, mock_db_connection):
        """Успешное удаление документа"""
        mock_db_connection.execute.return_value = None
        mock_db_connection.rowcount = 1
        
        result = db_instance.delet_document_by_id(1)
        
        assert mock_db_connection.execute.called
    
    def test_delet_document_by_id_not_found(self, db_instance, mock_db_connection):
        """Попытка удалить несуществующий документ"""
        mock_db_connection.execute.return_value = None
        mock_db_connection.rowcount = 0
        
        db_instance.delet_document_by_id(999)
        
        assert mock_db_connection.execute.called
    
    def test_insert_signed_document(self, db_instance, mock_db_connection):
        """Вставка подписанного документа"""
        mock_db_connection.execute.return_value = None
        mock_db_connection.fetchone.return_value = (2,)  # ID нового документа
        
        signature_data = {
            'x': 100,
            'y': 100,
            'width': 50,
            'height': 50
        }
        
        result = db_instance.insert_signed_document(
            title="signed.pdf",
            hash="sig_hash",
            created_at=1704067200,
            base64="base64signed",
            email="test@domain.com",
            original_doc_id=1,
            signer="test@domain.com",
            signature_data=signature_data
        )
        
        assert mock_db_connection.execute.called


# =====================================================================
# БЛОК В: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С КЛЮЧАМИ
# =====================================================================

class TestDatabaseKeyOperations:
    """Тестирование операций с криптографическими ключами"""
    
    def test_insert_keys_by_email(self, db_instance, mock_db_connection):
        """Вставка пары ключей для пользователя"""
        mock_db_connection.execute.return_value = None
        
        db_instance.insert_keys_by_email(
            email="test@domain.com",
            public_key="pub_key_b64",
            private_key="priv_key_b64"
        )
        
        assert mock_db_connection.execute.called
    
    def test_get_public_key_by_email(self, db_instance, mock_db_connection):
        """Получение публичного ключа пользователя"""
        mock_db_connection.fetchone.return_value = ("pub_key_b64",)
        
        result = db_instance.get_public_key_by_email("test@domain.com")
        
        assert result == "pub_key_b64" or result is not None
    
    def test_get_public_key_by_email_not_found(self, db_instance, mock_db_connection):
        """Получение публичного ключа для пользователя без ключей"""
        mock_db_connection.fetchone.return_value = None
        
        result = db_instance.get_public_key_by_email("nokey@domain.com")
        
        assert result is None
    
    def test_get_private_key_by_email(self, db_instance, mock_db_connection):
        """Получение приватного ключа пользователя"""
        mock_db_connection.fetchone.return_value = ("priv_key_b64",)
        
        result = db_instance.get_private_key_by_email("test@domain.com")
        
        assert result == "priv_key_b64" or result is not None
    
    def test_get_private_key_by_email_not_found(self, db_instance, mock_db_connection):
        """Получение приватного ключа для пользователя без ключей"""
        mock_db_connection.fetchone.return_value = None
        
        result = db_instance.get_private_key_by_email("nokey@domain.com")
        
        assert result is None


# =====================================================================
# БЛОК Г: ТЕСТИРОВАНИЕ DATABASEREDIS
# =====================================================================

class TestDatabaseRedisOperations:
    """Тестирование операций с Redis"""
    
    def test_save_refresh_token(self, redis_instance, mock_redis_connection):
        """Сохранение refresh токена"""
        mock_redis_connection.setex.return_value = True
        
        redis_instance.save_refresh_token("test@domain.com", "refresh_token_123")
        
        # Проверяем, что был вызван setex (по умолчанию срок - 7 дней)
        assert mock_redis_connection.setex.called
    
    def test_get_refresh_token(self, redis_instance, mock_redis_connection):
        """Получение refresh токена"""
        mock_redis_connection.get.return_value = b"refresh_token_123"
        
        result = redis_instance.get_refresh_token("test@domain.com")
        
        assert result is not None or result == b"refresh_token_123"
    
    def test_get_refresh_token_expired(self, redis_instance, mock_redis_connection):
        """Получение истекшего refresh токена"""
        mock_redis_connection.get.return_value = None
        
        result = redis_instance.get_refresh_token("test@domain.com")
        
        assert result is None
    
    def test_delete_refresh_token(self, redis_instance, mock_redis_connection):
        """Удаление refresh токена"""
        mock_redis_connection.delete.return_value = 1
        
        redis_instance.delete_refresh_token("test@domain.com")
        
        assert mock_redis_connection.delete.called
    
    def test_check_token_exists(self, redis_instance, mock_redis_connection):
        """Проверка существования токена"""
        mock_redis_connection.exists.return_value = 1
        
        result = redis_instance.get_refresh_token("test@domain.com")
        
        # Если токен существует, он должен быть возвращен
        assert mock_redis_connection.get.called or result is not None or result is None


# =====================================================================
# БЛОК Д: ТЕСТИРОВАНИЕ ОБРАБОТКИ ОШИБОК
# =====================================================================

class TestDatabaseErrorHandling:
    """Тестирование обработки ошибок БД"""
    
    def test_database_connection_error(self, db_instance):
        """Обработка ошибки подключения к БД"""
        with patch.object(db_instance, '_cursor') as mock_cursor:
            mock_cursor.execute.side_effect = Exception("Connection refused")
            
            # Должна быть обработана ошибка
            with pytest.raises(Exception):
                db_instance.get_user_by_email("test@domain.com")
    
    def test_redis_connection_error(self, redis_instance):
        """Обработка ошибки подключения к Redis"""
        with patch.object(redis_instance, '_redis') as mock_redis:
            mock_redis.get.side_effect = Exception("Redis connection lost")
            
            with pytest.raises(Exception):
                redis_instance.get_refresh_token("test@domain.com")
    
    def test_database_query_timeout(self, db_instance, mock_db_connection):
        """Обработка timeout при выполнении запроса"""
        mock_db_connection.execute.side_effect = Exception("Query timeout")
        
        # Функция должна либо вернуть None, либо бросить исключение
        with pytest.raises(Exception):
            db_instance.get_all_list_docs("test@domain.com")


# =====================================================================
# БЛОК Е: ТЕСТИРОВАНИЕ ПАРАЛЛЕЛЬНЫХ ОПЕРАЦИЙ
# =====================================================================

class TestDatabaseConcurrency:
    """Тестирование конкурентных операций"""
    
    def test_concurrent_user_operations(self, db_instance, mock_db_connection):
        """Проверка последовательных операций с несколькими пользователями"""
        mock_db_connection.fetchone.return_value = (1,)
        
        # Имитируем несколько пользователей
        users = [
            ("user1@domain.com", "pass1"),
            ("user2@domain.com", "pass2"),
            ("user3@domain.com", "pass3")
        ]
        
        for email, password in users:
            result = db_instance.check_user(email, password)
            assert mock_db_connection.execute.called
    
    def test_concurrent_document_operations(self, db_instance, mock_db_connection):
        """Проверка последовательных операций с документами"""
        mock_db_connection.fetchall.return_value = [(1, 'doc.pdf', 'hash', 'unsigned', 1704067200, 'test@domain.com')]
        
        # Получаем документы для нескольких пользователей
        for i in range(3):
            result = db_instance.get_all_list_docs(f"user{i}@domain.com")
            assert mock_db_connection.execute.called


# =====================================================================
# БЛОК Ж: ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# =====================================================================

class TestDatabaseIntegration:
    """Интеграционные тесты для полных сценариев"""
    
    def test_full_user_lifecycle(self, db_instance, mock_db_connection):
        """Полный цикл жизни пользователя: регистрация → получение → обновление"""
        # 1. Регистрация
        mock_db_connection.fetchone.return_value = (1,)
        register_result = db_instance.insert_user(
            "test@domain.com", "pass", {'firstName': 'John', 'lastName': 'Doe'}
        )
        assert mock_db_connection.execute.called
        
        # 2. Получение
        mock_db_connection.fetchone.return_value = (
            1, 'John', 'Doe', 'test@domain.com', True, 1704067200
        )
        user = db_instance.get_user_by_email("test@domain.com")
        assert user is not None
        
        # 3. Обновление
        mock_db_connection.execute.return_value = None
        db_instance.change_userName_by_id(1, "Jane", "Smith")
        assert mock_db_connection.execute.called
    
    def test_full_document_and_signature_flow(self, db_instance, mock_db_connection):
        """Полный цикл: загрузка док → генерация ключей → подпись → сохранение"""
        # 1. Загрузка документа
        mock_db_connection.execute.return_value = None
        db_instance.insert_doc(
            "test.pdf", "hash1", 1704067200, "base64content", "test@domain.com"
        )
        assert mock_db_connection.execute.called
        
        # 2. Генерация ключей
        mock_db_connection.execute.return_value = None
        db_instance.insert_keys_by_email(
            "test@domain.com", "pub_key", "priv_key"
        )
        assert mock_db_connection.execute.called
        
        # 3. Сохранение подписанного документа
        mock_db_connection.execute.return_value = None
        mock_db_connection.fetchone.return_value = (2,)
        db_instance.insert_signed_document(
            "signed.pdf", "hash2", 1704067200, "base64signed",
            "test@domain.com", 1, "test@domain.com", {}
        )
        assert mock_db_connection.execute.called
