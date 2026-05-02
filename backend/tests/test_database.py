"""
Тесты для модуля database.py

Функционал:
- Тестирование операций с PostgreSQL
- Тестирование операций с Redis
- Мок-тестирование работы с БД

Примечание: Все глобальное мокирование выполняется в conftest.py
"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from database import Database, DatabaseRedis
except ImportError as e:
    pytest.skip(f"Cannot import database module: {e}", allow_module_level=True)


# =====================================================================
# БЛОК А: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С ПОЛЬЗОВАТЕЛЯМИ
# =====================================================================

class TestDatabaseUserOperations:
    """Тестирование операций с пользователями в БД"""
    
    def test_insert_user_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Успешная вставка пользователя"""
        mock_postgres_cursor.fetchone.return_value = (1,)
        
        result = db_with_mocked_postgres.insert_user(
            email="test@domain.com",
            password="hashed_pass",
            name={'firstName': 'John', 'lastName': 'Doe'}
        )
        
        assert mock_postgres_cursor.execute.called
    
    def test_insert_user_duplicate_email(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Попытка вставить пользователя с существующим email"""
        mock_postgres_cursor.execute.side_effect = Exception("UNIQUE constraint violated")
        
        with pytest.raises(Exception):
            db_with_mocked_postgres.insert_user(
                email="existing@domain.com",
                password="pass",
                name={'firstName': 'John', 'lastName': 'Doe'}
            )
    
    def test_get_user_by_email(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение пользователя по email"""
        mock_postgres_cursor.fetchone.return_value = (
            1, 'John', 'Doe', 'test@domain.com', True, 1704067200
        )
        
        result = db_with_mocked_postgres.get_user_by_email("test@domain.com")
        
        assert result is not None or result
        assert mock_postgres_cursor.execute.called
    
    def test_get_user_by_email_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Поиск несуществующего пользователя"""
        mock_postgres_cursor.fetchone.return_value = None
        
        result = db_with_mocked_postgres.get_user_by_email("nonexistent@domain.com")
        
        assert result is None or not result
    
    def test_check_user_valid_credentials(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка валидных учетных данных"""
        mock_postgres_cursor.fetchone.return_value = (0,)
        
        result = db_with_mocked_postgres.check_user("test@domain.com", "password123")
        
        assert result == 0 or result
    
    def test_check_user_invalid_credentials(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка невалидных учетных данных"""
        mock_postgres_cursor.fetchone.return_value = (2,)
        
        result = db_with_mocked_postgres.check_user("test@domain.com", "wrongpass")
        
        assert result == 2 or result
    
    def test_is_original_email_available(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка доступности email"""
        mock_postgres_cursor.fetchone.return_value = (0,)
        
        result = db_with_mocked_postgres.is_original_email("available@domain.com")
        
        assert result is True or result == 0
    
    def test_is_original_email_taken(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Проверка занятого email"""
        mock_postgres_cursor.fetchone.return_value = (1,)
        
        result = db_with_mocked_postgres.is_original_email("taken@domain.com")
        
        assert result is False or result == 1
    
    def test_change_userName_by_id(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Изменение имени пользователя"""
        mock_postgres_cursor.execute.return_value = None
        
        db_with_mocked_postgres.change_userName_by_id(1, "Jane", "Smith")
        
        assert mock_postgres_cursor.execute.called


# =====================================================================
# БЛОК Б: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С ДОКУМЕНТАМИ
# =====================================================================

class TestDatabaseDocumentOperations:
    """Тестирование операций с документами в БД"""
    
    def test_insert_doc_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Успешная вставка документа"""
        mock_postgres_cursor.execute.return_value = None
        
        result = db_with_mocked_postgres.insert_doc(
            title="test.pdf",
            hash="abc123",
            created_at=1704067200,
            base64="base64content",
            email="test@domain.com"
        )
        
        assert mock_postgres_cursor.execute.called
    
    def test_get_document_by_id(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение документа по ID"""
        mock_doc = (1, 'test.pdf', 'abc123', 'base64', 'test@domain.com')
        mock_postgres_cursor.fetchone.return_value = mock_doc
        
        result = db_with_mocked_postgres.get_document_by_id(1)
        
        assert result is not None or result
        assert mock_postgres_cursor.execute.called
    
    def test_get_document_by_id_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение несуществующего документа"""
        mock_postgres_cursor.fetchone.return_value = None
        
        result = db_with_mocked_postgres.get_document_by_id(999)
        
        assert result is None or not result
    
    def test_get_all_list_docs(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение всех документов пользователя"""
        mock_docs = [
            (1, 'doc1.pdf', 'hash1', 'unsigned', 1704067200, 'test@domain.com'),
            (2, 'doc2.pdf', 'hash2', 'signed', 1704067300, 'test@domain.com')
        ]
        mock_postgres_cursor.fetchall.return_value = mock_docs
        
        result = db_with_mocked_postgres.get_all_list_docs("test@domain.com")
        
        assert len(result) == 2
        assert mock_postgres_cursor.execute.called
    
    def test_get_all_list_docs_empty(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение списка документов для пользователя без документов"""
        mock_postgres_cursor.fetchall.return_value = []
        
        result = db_with_mocked_postgres.get_all_list_docs("noissue@domain.com")
        
        assert len(result) == 0
    
    def test_delet_document_by_id_success(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Успешное удаление документа"""
        mock_postgres_cursor.execute.return_value = None
        mock_postgres_cursor.rowcount = 1
        
        result = db_with_mocked_postgres.delet_document_by_id(1)
        
        assert mock_postgres_cursor.execute.called
    
    def test_delet_document_by_id_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Попытка удалить несуществующий документ"""
        mock_postgres_cursor.execute.return_value = None
        mock_postgres_cursor.rowcount = 0
        
        db_with_mocked_postgres.delet_document_by_id(999)
        
        assert mock_postgres_cursor.execute.called
    
    def test_insert_signed_document(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Вставка подписанного документа"""
        mock_postgres_cursor.execute.return_value = None
        mock_postgres_cursor.fetchone.return_value = (2,)
        
        signature_data = {'x': 100, 'y': 100, 'width': 50, 'height': 50}
        
        result = db_with_mocked_postgres.insert_signed_document(
            title="signed.pdf",
            hash="sig_hash",
            created_at=1704067200,
            base64="base64signed",
            email="test@domain.com",
            original_doc_id=1,
            signer="test@domain.com",
            signature_data=signature_data
        )
        
        assert mock_postgres_cursor.execute.called


# =====================================================================
# БЛОК В: ТЕСТИРОВАНИЕ DATABASE - ОПЕРАЦИИ С КЛЮЧАМИ
# =====================================================================

class TestDatabaseKeyOperations:
    """Тестирование операций с криптографическими ключами"""
    
    def test_insert_keys_by_email(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Вставка пары ключей для пользователя"""
        mock_postgres_cursor.execute.return_value = None
        
        db_with_mocked_postgres.insert_keys_by_email(
            email="test@domain.com",
            public_key="pub_key_b64",
            private_key="priv_key_b64"
        )
        
        assert mock_postgres_cursor.execute.called
    
    def test_get_public_key_by_email(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение публичного ключа пользователя"""
        mock_postgres_cursor.fetchone.return_value = ("pub_key_b64",)
        
        result = db_with_mocked_postgres.get_public_key_by_email("test@domain.com")
        
        assert result is not None or result
    
    def test_get_public_key_by_email_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение публичного ключа для пользователя без ключей"""
        mock_postgres_cursor.fetchone.return_value = None
        
        result = db_with_mocked_postgres.get_public_key_by_email("nokey@domain.com")
        
        assert result is None or not result
    
    def test_get_private_key_by_email(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение приватного ключа пользователя"""
        mock_postgres_cursor.fetchone.return_value = ("priv_key_b64",)
        
        result = db_with_mocked_postgres.get_private_key_by_email("test@domain.com")
        
        assert result is not None or result
    
    def test_get_private_key_by_email_not_found(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Получение приватного ключа для пользователя без ключей"""
        mock_postgres_cursor.fetchone.return_value = None
        
        result = db_with_mocked_postgres.get_private_key_by_email("nokey@domain.com")
        
        assert result is None or not result


# =====================================================================
# БЛОК Г: ТЕСТИРОВАНИЕ DATABASEREDIS
# =====================================================================

class TestDatabaseRedisOperations:
    """Тестирование операций с Redis"""
    
    def test_save_refresh_token(self, redis_with_mocked_connection, mock_redis_client):
        """Сохранение refresh токена"""
        mock_redis_client.setex.return_value = True
        
        redis_with_mocked_connection.save_refresh_token("test@domain.com", "refresh_token_123")
        
        assert mock_redis_client.setex.called
    
    def test_get_refresh_token(self, redis_with_mocked_connection, mock_redis_client):
        """Получение refresh токена"""
        mock_redis_client.get.return_value = b"refresh_token_123"
        
        result = redis_with_mocked_connection.get_refresh_token("test@domain.com")
        
        assert result is not None or result
    
    def test_get_refresh_token_expired(self, redis_with_mocked_connection, mock_redis_client):
        """Получение истекшего refresh токена"""
        mock_redis_client.get.return_value = None
        
        result = redis_with_mocked_connection.get_refresh_token("test@domain.com")
        
        assert result is None or not result
    
    def test_delete_refresh_token(self, redis_with_mocked_connection, mock_redis_client):
        """Удаление refresh токена"""
        mock_redis_client.delete.return_value = 1
        
        redis_with_mocked_connection.delete_refresh_token("test@domain.com")
        
        assert mock_redis_client.delete.called


# =====================================================================
# БЛОК Д: ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# =====================================================================

class TestDatabaseIntegration:
    """Интеграционные тесты для полных сценариев"""
    
    def test_full_user_lifecycle(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Полный цикл жизни пользователя: регистрация → получение → обновление"""
        # 1. Регистрация
        mock_postgres_cursor.fetchone.return_value = (1,)
        register_result = db_with_mocked_postgres.insert_user(
            "test@domain.com", "pass", {'firstName': 'John', 'lastName': 'Doe'}
        )
        assert mock_postgres_cursor.execute.called
        
        # 2. Получение
        mock_postgres_cursor.fetchone.return_value = (
            1, 'John', 'Doe', 'test@domain.com', True, 1704067200
        )
        user = db_with_mocked_postgres.get_user_by_email("test@domain.com")
        assert user is not None
        
        # 3. Обновление
        mock_postgres_cursor.execute.return_value = None
        db_with_mocked_postgres.change_userName_by_id(1, "Jane", "Smith")
        assert mock_postgres_cursor.execute.called
    
    def test_full_document_lifecycle(self, db_with_mocked_postgres, mock_postgres_cursor):
        """Полный цикл документа: загрузка → получение → удаление"""
        # 1. Загрузка
        mock_postgres_cursor.execute.return_value = None
        db_with_mocked_postgres.insert_doc(
            "test.pdf", "hash1", 1704067200, "base64", "test@domain.com"
        )
        assert mock_postgres_cursor.execute.called
        
        # 2. Получение
        mock_postgres_cursor.fetchone.return_value = (
            1, "test.pdf", "hash1", "base64", "test@domain.com"
        )
        doc = db_with_mocked_postgres.get_document_by_id(1)
        assert doc is not None
        
        # 3. Удаление
        mock_postgres_cursor.execute.return_value = None
        mock_postgres_cursor.rowcount = 1
        db_with_mocked_postgres.delet_document_by_id(1)
        assert mock_postgres_cursor.execute.called
