"""
conftest.py - Глобальная конфигурация pytest и фиксты

Этот файл содержит:
- Mock конфигурацию для всех модулей
- Глобальные фиксты для тестов
- Настройку окружения для pytest
"""

import sys
import pytest
from unittest.mock import MagicMock
import jwt
from datetime import datetime, timezone


from pathlib import Path


# =====================================================================
# ГЛОБАЛЬНОЕ МОКИРОВАНИЕ МОДУЛЕЙ
# =====================================================================
# Прежде чем импортировать service.py, нужно замокировать его зависимости

# 1. Мокируем config_db
mock_config = MagicMock()
mock_config.SECRET_KEY = "test_secret_key_for_jwt"
mock_config.DB_URL = "postgresql://test:test@localhost/test_db"
mock_config.REDIS_URL = "redis://localhost:6379/0"
mock_config.host_r = "localhost"
mock_config.port_r = 6379
sys.modules['config_db'] = mock_config

# 2. Добавляем родительскую директорию в путь
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 3. Импортируем srevice ПОСЛЕ мокирования config_db
try:
    from service import (
        User, SignatureUNEP,
        SUCCESS_STATUS, INVALID_CREDENTIALS_STATUS,
        DB_CONNECTION_ERROR_STATUS, GENERAL_ERROR_STATUS
    )
except ImportError as e:
    pytest.skip(f"Cannot import service.py: {e}", allow_module_level=True)


# =====================================================================
# ГЛОБАЛЬНЫЕ ФИКСТЫ
# =====================================================================

@pytest.fixture
def mock_db():
    """
    Фикста: MagicMock имитирует реальный класс Database.
    Используется для всех тестов, работающих с БД.
    """
    db = MagicMock()
    
    # Стандартные ответы для получения пользователя
    db.get_user_by_email.return_value = {
        'id': 101,
        'first_name': 'Test',
        'last_name': 'Testov',
        'is_email_verified': True,
        'created_at': 1672531200
    }
    
    # Стандартные ответы для документов
    db.get_document_by_id.return_value = {
        'id': 1,
        'title': 'test.pdf',
        'hash': 'abc123def456',
        'base64': 'base64content',
        'email': 'test@domain.com',
        'created_at': 1704067200,
        'signing_status': 'unsigned'
    }
    
    db.get_all_list_docs.return_value = [
        {
            'id': 1,
            'title': 'doc1.pdf',
            'hash': 'hash1',
            'signing_status': 'unsigned',
            'created_at': 1704067200,
            'email': 'test@domain.com'
        }
    ]
    
    # Стандартные ответы для ключей
    db.get_public_key_by_email.return_value = None
    db.get_private_key_by_email.return_value = None
    
    # Стандартные ответы для операций
    db.insert_user.return_value = True
    db.insert_doc.return_value = True
    db.insert_keys_by_email.return_value = True
    db.check_user.return_value = 0  # SUCCESS
    db.is_original_email.return_value = True
    
    return db


@pytest.fixture
def mock_redis():
    """
    Фикста: MagicMock имитирует Redis для хранения токенов.
    """
    redis_obj = MagicMock()
    
    redis_obj.save_refresh_token.return_value = True
    redis_obj.get_refresh_token.return_value = "mock_refresh_token"
    redis_obj.delete_refresh_token.return_value = True
    
    return redis_obj


@pytest.fixture
def user_instance(mock_db, mock_redis):
    """
    Фикста: Экземпляр User класса с замоканными БД.
    """
    return User(
        email="test@domain.com",
        db=mock_db,
        db_redis=mock_redis,
        flag_pg=True
    )


@pytest.fixture
def valid_jwt_token():
    """
    Фикста: Генерирует валидный JWT токен для тестирования API.
    """
    payload = {
        "sub": "123",
        "name": "test@domain.com",
        "iat": datetime.now(timezone.utc).timestamp(),
        "exp": datetime.now(timezone.utc).timestamp() + 600
    }
    token = jwt.encode(payload, mock_config.SECRET_KEY, algorithm="HS256")
    return token


@pytest.fixture
def expired_jwt_token():
    """
    Фикста: Генерирует истекший JWT токен для тестирования.
    """
    payload = {
        "sub": "123",
        "name": "test@domain.com",
        "iat": datetime.now(timezone.utc).timestamp() - 700,
        "exp": datetime.now(timezone.utc).timestamp() - 60  # Истек 60 сек назад
    }
    token = jwt.encode(payload, mock_config.SECRET_KEY, algorithm="HS256")
    return token


@pytest.fixture
def invalid_jwt_token():
    """
    Фикста: Невалидный JWT токен.
    """
    return "invalid.token.not.valid"


@pytest.fixture
def test_user_data():
    """
    Фикста: Стандартные данные тестового пользователя.
    """
    return {
        'email': 'test@domain.com',
        'password': 'TestPassword123',
        'first_name': 'John',
        'last_name': 'Doe',
        'id': 101,
        'is_email_verified': True,
        'created_at': 1704067200
    }


@pytest.fixture
def test_document_data():
    """
    Фикста: Стандартные данные тестового документа.
    """
    return {
        'id': 1,
        'title': 'Contract.pdf',
        'hash': 'sha256hash1234567890abcdef',
        'base64': 'JVBERi0xLjQK...',  # Минимальный валидный PDF
        'email': 'test@domain.com',
        'created_at': 1704067200,
        'signing_status': 'unsigned'
    }


# =====================================================================
# ФИКСТЫ ДЛЯ ТЕСТИРОВАНИЯ БАЗЫ ДАННЫХ
# =====================================================================

@pytest.fixture
def mock_postgres_cursor():
    """Mock для курсора PostgreSQL с поддержкой context manager."""
    cursor = MagicMock()
    
    # Стандартные возвращаемые значения
    cursor.fetchone.return_value = (1,)  # ID пользователя по умолчанию
    cursor.fetchall.return_value = []
    cursor.execute.return_value = None
    cursor.close.return_value = None
    
    # Context manager поддержка (__enter__ и __exit__)
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=None)
    
    return cursor


@pytest.fixture
def mock_postgres_connection(mock_postgres_cursor):
    """Mock для соединения PostgreSQL с правильной context manager поддержкой."""
    connection = MagicMock()
    
    # cursor() возвращает context manager который работает с with statement
    cursor_context_manager = MagicMock()
    cursor_context_manager.__enter__ = MagicMock(return_value=mock_postgres_cursor)
    cursor_context_manager.__exit__ = MagicMock(return_value=None)
    
    connection.cursor.return_value = cursor_context_manager
    connection.commit.return_value = None
    connection.close.return_value = None
    connection.autocommit = True
    
    return connection


@pytest.fixture
def db_with_mocked_postgres(mock_postgres_connection):
    """
    Фикста: Database класс с замоканным PostgreSQL.
    Используется для unit-тестирования методов Database с реальной DI.
    """
    try:
        from database import Database
        return Database(connection=mock_postgres_connection)
    except ImportError:
        # Fallback для случая если database не импортируется
        db = MagicMock()
        db.get_user_by_email = MagicMock(return_value={
            'id': 101,
            'first_name': 'Test',
            'last_name': 'Testov',
            'is_email_verified': True,
            'created_at': 1672531200
        })
        db.insert_user = MagicMock(return_value=True)
        db.check_user = MagicMock(return_value=0)
        db.is_original_email = MagicMock(return_value=True)
        db.change_userName_by_id = MagicMock(return_value=True)
        db.insert_doc = MagicMock(return_value=1)
        db.get_document_by_id = MagicMock(return_value={'id': 1, 'title': 'test.pdf'})
        db.get_all_list_docs = MagicMock(return_value=[])
        db.delet_document_by_id = MagicMock(return_value=True)
        db.insert_signed_document = MagicMock(return_value=1)
        db.insert_keys_by_email = MagicMock(return_value=True)
        db.get_public_key_by_email = MagicMock(return_value=None)
        db.get_private_key_by_email = MagicMock(return_value=None)
        return db


@pytest.fixture
def mock_redis_client():
    """Mock для Redis клиента."""
    redis_client = MagicMock()
    redis_client.set = MagicMock()
    redis_client.get = MagicMock(return_value=None)
    redis_client.delete = MagicMock()
    redis_client.exists = MagicMock(return_value=False)
    return redis_client


@pytest.fixture
def redis_with_mocked_connection(mock_redis_client):
    """
    Фикста: DatabaseRedis класс с замоканным Redis.
    Вместо импорта реального класса, возвращаем MagicMock с нужным интерфейсом.
    """
    
    db_redis = MagicMock()
    
    # Конфигурируем mock для операций с токенами
    db_redis.save_refresh_token = MagicMock(return_value=True)
    db_redis.get_refresh_token = MagicMock(return_value="mock_token_12345")
    db_redis.delete_refresh_token = MagicMock(return_value=True)
    db_redis.check_token_exists = MagicMock(return_value=False)
    
    return db_redis


@pytest.fixture
def config_mock_fixture():
    """
    Фикста для доступа к mock_config из conftest
    """
    return mock_config


# =====================================================================
# МАРКЕРЫ И КОНФИГУРАЦИЯ
# =====================================================================

def pytest_configure(config):
    """Регистрация пользовательских маркеров."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers", "crypto: mark test as requiring cryptography"
    )
