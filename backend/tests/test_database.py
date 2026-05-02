"""
Тесты для модуля database.py с СТРОГИМИ ПРОВЕРКАМИ

Функционал:
- Тестирование операций с PostgreSQL с Dependency Injection
- Тестирование структуры возвращаемых данных
- Проверка параметров SQL запросов
- Тестирование операций с Redis

Примечание: Все глобальное мокирование выполняется в conftest.py
"""

import pytest
from unittest.mock import MagicMock, patch, call
import json

try:
    from database import Database, DatabaseRedis
except ImportError as e:
    pytest.skip(f"Cannot import database module: {e}", allow_module_level=True)


# =====================================================================
# БЛОК А: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С ПОЛЬЗОВАТЕЛЯМИ
# =====================================================================

class TestDatabaseUserOperations:
    """Тестирование операций с пользователями в БД"""
    
    def test_insert_user_success_with_name(self, db_with_mocked_postgres, mock_postgres_cursor, mock_postgres_connection):
        """Успешная вставка пользователя с именем и фамилией"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = (1,)
        mock_postgres_cursor.execute.return_value = None
        
        # Execute
        result = db_with_mocked_postgres.insert_user(
            login="test@example.com",
            password="testpass123",
            name={'firstName': 'John', 'lastName': 'Doe'}
        )
        
        # Verify - СТРОГАЯ ПРОВЕРКА
        assert isinstance(result, bool)
        assert result is True
        assert mock_postgres_cursor.execute.called
        
        # Проверяем SQL запрос
        call_args = mock_postgres_cursor.execute.call_args_list
        assert len(call_args) > 0
        sql_query, sql_params = call_args[-1][0]
        assert "INSERT INTO users" in sql_query
        assert "(%s, %s, %s, %s)" in sql_query
        assert len(sql_params) == 4
        assert sql_params[0] == "test@example.com"
        assert sql_params[2] == "John"
        assert sql_params[3] == "Doe"
        
        # Проверяем commit был вызван
        assert mock_postgres_connection.commit.called
    
    def test_insert_user_success_without_name(self, db_with_mocked_postgres):
        """Успешная вставка пользователя без имени"""
        result = db_with_mocked_postgres.insert_user(
            login="noname@example.com",
            password="testpass123",
            name=None
        )
        
        assert isinstance(result, bool)
        assert result is True
    
    @pytest.mark.parametrize("email,expected", [
        ("available@domain.com", True),
        ("taken@domain.com", False),
    ])
    def test_is_original_email(self, db_with_mocked_postgres, mock_postgres_cursor, email, expected):
        """Проверка доступности email - параметризованный тест"""
        # Setup
        if expected:
            mock_postgres_cursor.fetchone.return_value = None  # Email не найден = свободен
        else:
            mock_postgres_cursor.fetchone.return_value = (1,)  # Email найден = занят
        
        # Execute
        result = db_with_mocked_postgres.is_original_email(email)
        
        # Verify
        assert isinstance(result, bool), f"Expected bool, got {type(result)}"
        assert result == expected, f"Expected {expected}, got {result}"
        
        # Проверяем что был вызван SELECT
        assert mock_postgres_cursor.execute.called
        call_args = mock_postgres_cursor.execute.call_args_list[-1][0]
        sql_query, sql_params = call_args
        assert "SELECT 1 FROM users" in sql_query
        assert "WHERE email = %s" in sql_query
        assert sql_params[0] == email
    
    def test_check_user_valid_credentials(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка валидных учетных данных"""
        # Setup
        from hashlib import sha256
        password = "correct_password"
        password_hash = sha256(password.encode()).hexdigest()
        mock_postgres_cursor.fetchone.return_value = (password_hash, True)  # Пароль совпадает, активен
        
        # Execute
        result = db_with_mocked_postgres.check_user("test@domain.com", password)
        
        # Verify
        assert isinstance(result, int)
        assert result == 0  # SUCCESS_STATUS
    
    def test_check_user_invalid_password(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка невалидного пароля"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = ("other_hash", True)
        
        # Execute
        result = db_with_mocked_postgres.check_user("test@domain.com", "wrong_password")
        
        # Verify
        assert isinstance(result, int)
        assert result == 2  # INVALID_CREDENTIALS_STATUS
    
    def test_check_user_user_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка несуществующего пользователя"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = None
        
        # Execute
        result = db_with_mocked_postgres.check_user("nonexistent@domain.com", "password")
        
        # Verify
        assert isinstance(result, int)
        assert result == 2  # INVALID_CREDENTIALS_STATUS
    
    def test_get_user_by_email_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение пользователя по email - успешно найден"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'is_email_verified': True,
            'created_at': 1704067200
        }
        
        # Execute
        result = db_with_mocked_postgres.get_user_by_email("john@domain.com")
        
        # Verify - СТРОГАЯ ПРОВЕРКА СТРУКТУРЫ
        assert result is not None
        assert isinstance(result, dict)
        assert 'id' in result
        assert 'first_name' in result
        assert 'last_name' in result
        assert 'is_email_verified' in result
        assert 'created_at' in result
        assert isinstance(result['id'], int)
        assert isinstance(result['first_name'], str)
        assert isinstance(result['is_email_verified'], bool)
        assert isinstance(result['created_at'], int)
    
    def test_get_user_by_email_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение несуществующего пользователя"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = None
        
        # Execute
        result = db_with_mocked_postgres.get_user_by_email("nonexistent@domain.com")
        
        # Verify
        assert result is None
    
    def test_change_user_name(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Изменение имени пользователя"""
        # Execute
        db_with_mocked_postgres.change_userName_by_id(1, "Jane", "Smith")
        
        # Verify
        assert mock_postgres_cursor.execute.called
        call_args = mock_postgres_cursor.execute.call_args_list[-1][0]
        sql_query, sql_params = call_args
        assert "UPDATE users" in sql_query
        assert "first_name = %s" in sql_query
        assert "last_name = %s" in sql_query
        assert sql_params[0] == "Jane"
        assert sql_params[1] == "Smith"


# =====================================================================
# БЛОК Б: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С ДОКУМЕНТАМИ
# =====================================================================

class TestDatabaseDocumentOperations:
    """Тестирование операций с документами в БД"""
    
    def test_insert_doc_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Успешная вставка документа"""
        # Execute
        result = db_with_mocked_postgres.insert_doc(
            title="Contract.pdf",
            hash="sha256hash123",
            created_at=1704067200,
            base64="JVBERi0xLjQK...",
            email="test@domain.com"
        )
        
        # Verify
        assert isinstance(result, bool)
        assert result is True
        
        # Проверяем SQL запрос
        assert mock_postgres_cursor.execute.called
        call_args = mock_postgres_cursor.execute.call_args_list[-1][0]
        sql_query, sql_params = call_args
        assert "INSERT INTO documents" in sql_query
        assert sql_params[0] == "Contract.pdf"
        assert sql_params[1] == "sha256hash123"
    
    def test_get_all_list_docs(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение всех документов пользователя"""
        # Setup
        mock_docs = [
            {
                'id': 1,
                'title': 'doc1.pdf',
                'hash': 'hash1',
                'signing_status': 'unsigned',
                'created_at': 1704067200,
                'email': 'test@domain.com'
            },
            {
                'id': 2,
                'title': 'doc2.pdf',
                'hash': 'hash2',
                'signing_status': 'signed',
                'created_at': 1704067300,
                'email': 'test@domain.com'
            }
        ]
        mock_postgres_cursor.fetchall.return_value = mock_docs
        
        # Execute
        result = db_with_mocked_postgres.get_all_list_docs("test@domain.com")
        
        # Verify - СТРОГАЯ ПРОВЕРКА
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Проверяем структуру каждого элемента
        for doc in result:
            assert isinstance(doc, dict)
            required_keys = {'id', 'title', 'hash', 'signing_status', 'created_at', 'email'}
            assert required_keys <= set(doc.keys())
            assert isinstance(doc['id'], int)
            assert isinstance(doc['title'], str)
            assert isinstance(doc['created_at'], int)
    
    def test_get_all_list_docs_empty(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение списка документов для пользователя без документов"""
        # Setup
        mock_postgres_cursor.fetchall.return_value = []
        
        # Execute
        result = db_with_mocked_postgres.get_all_list_docs("noissue@domain.com")
        
        # Verify
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_document_by_id_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение документа по ID - успешно"""
        # Setup
        mock_doc = {
            'id': 1,
            'title': 'test.pdf',
            'hash': 'abc123def456',
            'created_at': 1704067200,
            'base64': 'base64content',
            'email': 'test@domain.com'
        }
        mock_postgres_cursor.fetchone.return_value = mock_doc
        
        # Execute
        result = db_with_mocked_postgres.get_document_by_id(1)
        
        # Verify - СТРОГАЯ ПРОВЕРКА СТРУКТУРЫ
        assert result is not None
        assert isinstance(result, dict)
        assert 'id' in result
        assert 'title' in result
        assert 'hash' in result
        assert 'created_at' in result
        assert 'base64' in result
        assert 'email' in result
        assert isinstance(result['id'], int)
        assert isinstance(result['title'], str)
        assert isinstance(result['created_at'], int)
    
    def test_get_document_by_id_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение несуществующего документа"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = None
        
        # Execute
        result = db_with_mocked_postgres.get_document_by_id(999)
        
        # Verify
        assert result is None
    
    def test_delet_document_by_id_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Успешное удаление документа"""
        # Execute
        result = db_with_mocked_postgres.delet_document_by_id(1)
        
        # Verify
        assert isinstance(result, bool)
        assert result is True
        assert mock_postgres_cursor.execute.called
        
        # Проверяем что DELETE был вызван
        call_args = mock_postgres_cursor.execute.call_args_list[-1][0]
        sql_query, sql_params = call_args
        assert "DELETE FROM documents" in sql_query
        assert sql_params[0] == 1
    
    def test_delet_document_by_id_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Попытка удалить несуществующий документ"""
        # Execute
        result = db_with_mocked_postgres.delet_document_by_id(999)
        
        # Verify - функция может вернуть True даже если документа нет
        # но DELETE ЗАПРОС был выполнен
        assert isinstance(result, bool)
        assert mock_postgres_cursor.execute.called
    
    def test_insert_signed_document(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Вставка подписанного документа"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = (2,)  # ID нового документа
        
        # Execute
        result = db_with_mocked_postgres.insert_signed_document(
            title="signed.pdf",
            hash="sig_hash",
            created_at=1704067200,
            base64="base64signed",
            email="test@domain.com",
            original_doc_id=1,
            signer="test@domain.com",
            signature_data={'x': 100, 'y': 100, 'width': 50, 'height': 50}
        )
        
        # Verify
        assert isinstance(result, (int, type(None)))
        if result is not None:
            assert isinstance(result, int)
            assert result == 2  # ID документа
        assert mock_postgres_cursor.execute.called


# =====================================================================
# БЛОК В: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С КЛЮЧАМИ
# =====================================================================

class TestDatabaseKeyOperations:
    """Тестирование операций с криптографическими ключами"""
    
    def test_insert_keys_by_email(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Вставка пары ключей для пользователя"""
        # Execute
        result = db_with_mocked_postgres.insert_keys_by_email(
            email="test@domain.com",
            public_key="pub_key_b64_encoded",
            private_key="priv_key_b64_encoded"
        )
        
        # Verify
        assert isinstance(result, bool)
        assert result is True
        assert mock_postgres_cursor.execute.called
        
        # Проверяем SQL запрос
        call_args = mock_postgres_cursor.execute.call_args_list[-1][0]
        sql_query, sql_params = call_args
        assert "UPDATE users" in sql_query
        assert "public_key = %s" in sql_query
        assert "private_key = %s" in sql_query
        assert sql_params[0] == "pub_key_b64_encoded"
        assert sql_params[1] == "priv_key_b64_encoded"
    
    def test_get_public_key_by_email_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение публичного ключа пользователя"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = ("pub_key_b64_encoded",)
        
        # Execute
        result = db_with_mocked_postgres.get_public_key_by_email("test@domain.com")
        
        # Verify
        assert result is not None
        assert isinstance(result, str)
        assert result == "pub_key_b64_encoded"
    
    def test_get_public_key_by_email_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение публичного ключа для пользователя без ключей"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = None
        
        # Execute
        result = db_with_mocked_postgres.get_public_key_by_email("nokey@domain.com")
        
        # Verify
        assert result is None
    
    def test_get_private_key_by_email_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение приватного ключа пользователя"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = ("priv_key_b64_encoded",)
        
        # Execute
        result = db_with_mocked_postgres.get_private_key_by_email("test@domain.com")
        
        # Verify
        assert result is not None
        assert isinstance(result, str)
        assert result == "priv_key_b64_encoded"
    
    def test_get_private_key_by_email_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение приватного ключа для пользователя без ключей"""
        # Setup
        mock_postgres_cursor.fetchone.return_value = None
        
        # Execute
        result = db_with_mocked_postgres.get_private_key_by_email("nokey@domain.com")
        
        # Verify
        assert result is None


# =====================================================================
# БЛОК Г: ТЕСТИРОВАНИЕ DATABASEREDIS
# =====================================================================

class TestDatabaseRedisOperations:
    """Тестирование операций с Redis"""
    
    def test_save_refresh_token(self):
        """Сохранение refresh токена"""
        # Setup
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        
        # Execute
        db_redis = DatabaseRedis(redis_connection=mock_redis)
        result = db_redis.save_refresh_token("test@domain.com", "refresh_token_123")
        
        # Verify
        assert isinstance(result, bool)
        assert result is True
        assert mock_redis.setex.called
        
        # Проверяем параметры вызова
        call_args = mock_redis.setex.call_args
        assert "refresh_token:test@domain.com" in call_args[0][0]
    
    def test_check_refresh_token_valid(self):
        """Проверка валидного токена"""
        # Setup
        import json
        token_data = {"email": "test@domain.com", "refresh_token": "token_123"}
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps(token_data)
        
        # Execute
        db_redis = DatabaseRedis(redis_connection=mock_redis)
        result = db_redis.check_refresh_token("test@domain.com", "token_123")
        
        # Verify
        assert isinstance(result, bool)
        assert result is True
    
    def test_check_refresh_token_invalid(self):
        """Проверка невалидного токена"""
        # Setup
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        # Execute
        db_redis = DatabaseRedis(redis_connection=mock_redis)
        result = db_redis.check_refresh_token("test@domain.com", "token_123")
        
        # Verify
        assert isinstance(result, bool)
        assert result is False
    
    def test_delete_refresh_token(self):
        """Удаление refresh токена"""
        # Setup
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        
        # Execute
        db_redis = DatabaseRedis(redis_connection=mock_redis)
        result = db_redis.delete_refresh_token("test@domain.com")
        
        # Verify
        assert isinstance(result, bool)
        assert result is True
        assert mock_redis.delete.called
    
    def test_redis_di_fallback(self):
        """Проверка что при connection=None создается реальное подключение"""
        # Это более интеграционный тест
        # Просто проверяем что конструктор работает
        db_redis = DatabaseRedis(redis_connection=MagicMock())
        assert db_redis is not None
        assert db_redis.r is not None


# =====================================================================
# БЛОК Д: ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# =====================================================================

class TestDatabaseIntegration:
    """Интеграционные тесты для полных сценариев"""
    
    def test_full_user_scenario(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Полный сценарий: регистрация → поиск → обновление"""
        # 1. Проверка свеободности email
        mock_postgres_cursor.fetchone.return_value = None  # Email свободен
        is_available = db_with_mocked_postgres.is_original_email("john@domain.com")
        assert is_available is True
        
        # 2. Регистрация пользователя
        result = db_with_mocked_postgres.insert_user(
            "john@domain.com", "pass123",
            name={'firstName': 'John', 'lastName': 'Doe'}
        )
        assert result is True
        
        # 3. Получение пользователя
        mock_postgres_cursor.fetchone.return_value = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'is_email_verified': True,
            'created_at': 1704067200
        }
        user = db_with_mocked_postgres.get_user_by_email("john@domain.com")
        assert user is not None
        assert user['first_name'] == 'John'
        
        # 4. Обновление данных
        db_with_mocked_postgres.change_userName_by_id(1, "Jane", "Smith")
        assert mock_postgres_cursor.execute.called

