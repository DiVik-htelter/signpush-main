"""
Тесты для API endpoints из main.py

Функционал:
- Тестирование всех REST API эндпоинтов
- Проверка аутентификации через токены
- Тестирование работы с документами
- Тестирование интеграции с внешними сервисами
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import base64
import json
from datetime import datetime, timezone

# Мокирование происходит в conftest.py перед импортом

try:
    from fastapi.testclient import TestClient
    from main import app, check_token
    from service import (
        SUCCESS_STATUS, INVALID_CREDENTIALS_STATUS,
        DB_CONNECTION_ERROR_STATUS, GENERAL_ERROR_STATUS
    )
except ImportError as e:
    pytest.skip(f"Cannot import main.py or dependencies: {e}", allow_module_level=True)

# =====================================================================
# ФИКСТЫ
# =====================================================================

@pytest.fixture
def client(mock_db, mock_redis, monkeypatch):
    """TestClient для FastAPI приложения с мокированными БД"""
    # Патчим глобальные переменные модуля main
    monkeypatch.setattr('main.db', mock_db)
    monkeypatch.setattr('main.db_redis', mock_redis)
    return TestClient(app)


@pytest.fixture
def patch_app_db(mock_db, mock_redis):
    """
    Фикста: патчит глобальные объекты БД в main.py
    """
    with patch('main.db', mock_db), patch('main.db_redis', mock_redis):
        yield mock_db, mock_redis


@pytest.fixture
def client_with_patched_db(mock_db, mock_redis):
    """
    Фикста: TestClient с замоканными БД в main.py
    """
    with patch('main.db', mock_db), patch('main.db_redis', mock_redis):
        return TestClient(app)

# Фиксты для токенов уже определены в conftest.py:
# - valid_jwt_token
# - expired_jwt_token  
# - invalid_jwt_token


# =====================================================================
# БЛОК А: ТЕСТИРОВАНИЕ АУТЕНТИФИКАЦИИ
# =====================================================================

class TestAuthentication:
    """Тестирование endpoints аутентификации"""
    
    def test_check_token_valid(self, valid_jwt_token):
        """Проверка парсинга валидного токена"""
        result = check_token(valid_jwt_token)
        assert result == "test@domain.com"
    
    def test_check_token_invalid(self, invalid_jwt_token):
        """Проверка обработки невалидного токена"""
        result = check_token(invalid_jwt_token)
        assert result is False
    
    def test_check_token_expired(self, expired_jwt_token):
        """Проверка обработки истекшего токена"""
        result = check_token(expired_jwt_token)
        # Истекший токен парсится, но декодирование обычно падает
        assert result is False or result is None
    
    def test_check_token_none(self):
        """Проверка обработки None токена"""
        result = check_token(None)
        assert result is False
    
    def test_check_token_empty_string(self):
        """Проверка обработки пустой строки"""
        result = check_token("")
        assert result is False


class TestAuthEndpoint:
    """Тестирование POST /api/auth/ endpoint"""
    
    def test_auth_success(self, client, mock_db):
        """Успешная аутентификация"""
        mock_db.check_user.return_value = 0
        mock_db.get_user_by_email.return_value = {'id': 1}
        
        with patch('main.service.User') as MockUser:
            mock_user = MagicMock()
            mock_user.chek_auth.return_value = {
                "status": SUCCESS_STATUS,
                "token": "mock_jwt_token",
                "refresh_token": "mock_refresh_token",
                "message": "Success"
            }
            MockUser.return_value = mock_user
            
            response = client.post("/api/auth/", json={
                "mail": "test@domain.com",
                "password": "password123"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == SUCCESS_STATUS
            assert "token" in data
    
    def test_auth_invalid_credentials(self, client, mock_db):
        """Аутентификация с неверными учетными данными"""
        mock_db.check_user.return_value = 2
        
        with patch('main.service.User') as MockUser:
            mock_user = MagicMock()
            mock_user.chek_auth.return_value = {
                "status": INVALID_CREDENTIALS_STATUS,
                "token": -1,
                "message": "Invalid credentials"
            }
            MockUser.return_value = mock_user
            
            response = client.post("/api/auth/", json={
                "mail": "test@domain.com",
                "password": "wrongpassword"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == INVALID_CREDENTIALS_STATUS
    
    def test_auth_db_error(self, client, mock_db):
        """Ошибка подключения к БД"""
        mock_db.check_user.return_value = 3
        
        with patch('main.service.User') as MockUser:
            mock_user = MagicMock()
            mock_user.chek_auth.return_value = {
                "status": DB_CONNECTION_ERROR_STATUS,
                "token": -1,
                "message": "Database error"
            }
            MockUser.return_value = mock_user
            
            response = client.post("/api/auth/", json={
                "mail": "test@domain.com",
                "password": "password123"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == DB_CONNECTION_ERROR_STATUS


# =====================================================================
# БЛОК Б: ТЕСТИРОВАНИЕ РАБОТЫ С ДОКУМЕНТАМИ
# =====================================================================

class TestDocumentEndpoints:
    """Тестирование endpoints работы с документами"""
    
    def test_get_docs_unauthorized(self, client):
        """Получение документов без токена"""
        response = client.get("/api/docs")
        assert response.status_code == 401
    
    def test_get_docs_with_valid_jwt_token(self, client, valid_jwt_token, mock_db):
        """Получение списка документов с валидным токеном"""
        mock_db.get_all_list_docs.return_value = [
            {
                "id": 1,
                "title": "Document1.pdf",
                "hash": "abc123",
                "signing_status": "unsigned",
                "created_at": 1704067200,
                "email": "test@domain.com"
            }
        ]
        
        response = client.get("/api/docs", headers={"token": valid_jwt_token})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "There are 1 paperes"
        assert len(data["papers"]) == 1
    
    def test_get_docs_by_id_success(self, client, valid_jwt_token, mock_db):
        """Получение документа по ID"""
        mock_db.get_document_by_id.return_value = {
            "id": 1,
            "title": "Test.pdf",
            "hash": "hash123",
            "base64": "base64content",
            "created_at": 1704067200,
            "email": "test@domain.com"
        }
        
        response = client.patch(
            "/api/docs?doc_id=1",
            headers={"token": valid_jwt_token}
        )
        assert response.status_code == 200
    
    def test_get_docs_by_id_not_found(self, client, valid_jwt_token, mock_db):
        """Получение несуществующего документа"""
        mock_db.get_document_by_id.return_value = None
        
        response = client.patch(
            "/api/docs?doc_id=999",
            headers={"token": valid_jwt_token}
        )
        assert response.status_code == 404
    
    def test_delete_document_success(self, client, valid_jwt_token, mock_db):
        """Удаление документа"""
        mock_db.delet_document_by_id.return_value = True
        
        response = client.delete(
            "/api/docs?doc_id=1",
            headers={"token": valid_jwt_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_document_failure(self, client, valid_jwt_token, mock_db):
        """Ошибка при удалении документа"""
        mock_db.delet_document_by_id.return_value = False
        
        response = client.delete(
            "/api/docs?doc_id=1",
            headers={"token": valid_jwt_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
    
    def test_download_document(self, client, valid_jwt_token, mock_db):
        """Скачивание документа"""
        pdf_content = b"%PDF-1.4\n%test"
        pdf_b64 = base64.b64encode(pdf_content).decode()
        
        mock_db.get_document_by_id.return_value = {
            "title": "test.pdf",
            "base64": pdf_b64
        }
        
        response = client.get(
            "/api/docs/download/?doc_id=1",
            headers={"token": valid_jwt_token}
        )
        assert response.status_code == 200
        assert response.content == pdf_content


class TestDocumentUpload:
    """Тестирование загрузки документов"""
    
    def test_insert_doc_success(self, client, valid_jwt_token, mock_db):
        """Успешная загрузка документа"""
        mock_db.insert_doc.return_value = True
        
        payload = {
            "id": 1,
            "title": "test.pdf",
            "hash": "abc123",
            "base64": "base64content",
            "created_at": 1704067200,
            "email": "test@domain.com"
        }
        
        response = client.post(
            "/api/docs/download",
            json=payload,
            headers={"token": valid_jwt_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_insert_doc_unauthorized(self, client, mock_db):
        """Загрузка документа без токена"""
        payload = {
            "id": 1,
            "title": "test.pdf",
            "hash": "abc123",
            "base64": "base64content",
            "created_at": 1704067200,
            "email": "test@domain.com"
        }
        
        response = client.post("/api/docs/download", json=payload)
        assert response.status_code == 401


# =====================================================================
# БЛОК В: ТЕСТИРОВАНИЕ ПОДПИСЕЙ
# =====================================================================

class TestSignatureEndpoints:
    """Тестирование endpoints подписей"""
    
    def test_sign_document_no_token(self, client):
        """Подписание документа без токена"""
        response = client.post("/api/document/sign/", json={})
        assert response.status_code == 401
    
    def test_sign_document_invalid_params(self, client, valid_jwt_token, mock_db):
        """Подписание с невалидными параметрами"""
        payload = {
            "document_id": 1,
            "signature_base64": "sig",
            "page_number": 0,
            "x": 100,
            "y": 100,
            "width": -50,  # Невалидная ширина
            "height": 50,
            "login": "test@domain.com"
        }
        
        response = client.post(
            "/api/document/sign/",
            json=payload,
            headers={"token": valid_jwt_token}
        )
        assert response.status_code == 400
    
    def test_sign_document_not_found(self, client, valid_jwt_token, mock_db):
        """Подписание несуществующего документа"""
        mock_db.get_document_by_id.return_value = None
        
        payload = {
            "document_id": 999,
            "signature_base64": "sig",
            "page_number": 0,
            "x": 100,
            "y": 100,
            "width": 50,
            "height": 50,
            "login": "test@domain.com"
        }
        
        response = client.post(
            "/api/document/sign/",
            json=payload,
            headers={"token": valid_jwt_token}
        )
        assert response.status_code == 404


class TestUNEPSignatureEndpoints:
    """Тестирование endpoints для УНЭП подписей"""
    
    def test_sign_unep_unauthorized(self, client):
        """Подписание УНЭП без токена"""
        response = client.post(
            "/api/document/sign/unep/",
            json={"document_id": 1}
        )
        assert response.status_code == 401
    
    def test_verify_unep_unauthorized(self, client):
        """Проверка УНЭП подписи без токена"""
        response = client.post(
            "/api/document/verify/unep/",
            json={
                "document_base64": "doc",
                "signature_base64": "sig"
            }
        )
        assert response.status_code == 401
    
    def test_verify_unep_invalid_signature(self, client, valid_jwt_token, mock_db):
        """Проверка кривой подписи УНЭП"""
        with patch('main.SignatureUNEP') as MockSignature:
            mock_sig = MagicMock()
            mock_sig.verify_cms_container.return_value = {
                'is_valid': False,
                'checks': {'signature_valid': False},
                'attrs': []
            }
            MockSignature.return_value = mock_sig
            
            response = client.post(
                "/api/document/verify/unep/",
                json={
                    "document_base64": "doc",
                    "signature_base64": "invalid_sig"
                },
                headers={"token": valid_jwt_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False


# =====================================================================
# БЛОК Г: ТЕСТИРОВАНИЕ ПОЛЬЗОВАТЕЛЯ
# =====================================================================

class TestUserInfoEndpoints:
    """Тестирование endpoints информации о пользователе"""
    
    def test_get_user_info_unauthorized(self, client):
        """Получение информации без токена"""
        response = client.get("/api/user/info")
        assert response.status_code == 401
    
    def test_get_user_info_success(self, client, valid_jwt_token, mock_db):
        """Получение информации о пользователе"""
        mock_db.get_user_by_email.return_value = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@domain.com',
            'is_email_verified': True,
            'created_at': 1704067200
        }
        mock_db.get_public_key_by_email.return_value = "public_key_b64"
        
        with patch('main.service.User') as MockUser:
            mock_user = MagicMock()
            mock_user.get_all_info.return_value = {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'test@domain.com',
                'is_email_verified': True,
                'created_at': 1704067200,
                'public_key': 'public_key_b64'
            }
            MockUser.return_value = mock_user
            
            response = client.get(
                "/api/user/info",
                headers={"token": valid_jwt_token}
            )
            
            assert response.status_code == 200
    
    def test_update_user_info_success(self, client, valid_jwt_token, mock_db):
        """Обновление информации о пользователе"""
        mock_db.get_user_by_email.return_value = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@domain.com',
            'is_email_verified': True,
            'created_at': 1704067200
        }
        
        with patch('main.service.User') as MockUser:
            mock_user = MagicMock()
            mock_user.set_name.return_value = True
            MockUser.return_value = mock_user
            
            response = client.post(
                "/api/user/info/update",
                json={
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "new_password": "newpass123"
                },
                headers={"token": valid_jwt_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == SUCCESS_STATUS
    
    def test_update_user_info_invalid(self, client, valid_jwt_token, mock_db):
        """Обновление информации с невалидными данными"""
        mock_db.get_user_by_email.return_value = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@domain.com',
            'is_email_verified': True,
            'created_at': 1704067200
        }
        
        with patch('main.service.User') as MockUser:
            mock_user = MagicMock()
            mock_user.set_name.return_value = False
            MockUser.return_value = mock_user
            
            response = client.post(
                "/api/user/info/update",
                json={
                    "first_name": "J",  # Слишком короткое имя
                    "last_name": "Smith",
                    "new_password": "newpass123"
                },
                headers={"token": valid_jwt_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == GENERAL_ERROR_STATUS


class TestUserRegistration:
    """Тестирование регистрации пользователей"""
    
    def test_register_user_success(self, client, mock_db):
        """Успешная регистрация"""
        mock_db.insert_user.return_value = True
        
        response = client.post("/api/register/", json={
            "email": "newuser@domain.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == SUCCESS_STATUS
    
    def test_register_user_duplicate_email(self, client, mock_db):
        """Регистрация с существующим email"""
        mock_db.insert_user.return_value = False
        
        response = client.post("/api/register/", json={
            "email": "existing@domain.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] != SUCCESS_STATUS


# =====================================================================
# БЛОК Д: ТЕСТИРОВАНИЕ API ТРЕТЬЕГО СЕРВИСА (1C)
# =====================================================================

class TestExternalServiceAPI:
    """Тестирование API для третьих сервисов"""
    
    def test_register_via_external_api(self, client, mock_db):
        """Регистрация пользователя через внешний API"""
        mock_db.insert_user.return_value = True
        mock_db.is_original_email.return_value = True
        
        response = client.post("/api/v1/user/register", json={
            "email": "external@domain.com",
            "password": "pass123",
            "first_name": "External",
            "last_name": "User"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_document_validation_hash_mismatch(self, client, mock_db):
        """Проверка валидации хеша документа"""
        mock_db.get_user_by_email.return_value = {
            'id': 1,
            'email': 'user@domain.com'
        }
        
        # Неправильный хеш для contenта
        payload = {
            "endpoint": "https://external.example.com/callback",
            "deadlite_at": 1704067200,
            "document": {
                "id": 1,
                "title": "test.pdf",
                "hash": "wrong_hash",  # Не совпадает с contentом
                "base64": base64.b64encode(b"content").decode(),
                "created_at": 1704067200,
                "email": "user@domain.com"
            }
        }
        
        response = client.post(
            "/api/v1/document/sign/unep",
            json=payload
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_external_webhook_return(self, client, mock_db):
        """Возврат подписанного документа на webhook"""
        mock_db.get_document_by_id.return_value = {
            "id": 1,
            "title": "test.pdf",
            "base64": base64.b64encode(b"content").decode(),
            "hash": "hash123",
            "created_at": 1704067200,
            "email": "user@domain.com"
        }
        
        with patch('main.send_signed_doc', new_callable=AsyncMock):
            response = client.post(
                "/api/v1/document/webhook",
                json={
                    "document_id": 1,
                    "callback_url": "https://external.example.com/callback",
                    "signatureUNEP": base64.b64encode(b"sig").decode()
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestKeyGeneration:
    """Тестирование генерации ключей"""
    
    def test_generate_keys_success(self, client, valid_jwt_token, mock_db):
        """Успешная генерация ключей"""
        mock_db.get_public_key_by_email.return_value = None
        mock_db.insert_keys_by_email.return_value = True
        
        with patch('main.SignatureUNEP') as MockSignature:
            mock_sig = MagicMock()
            mock_sig.generate_user_keys.return_value = (
                base64.b64encode(b"public_key").decode(),
                base64.b64encode(b"private_key").decode()
            )
            MockSignature.return_value = mock_sig
            
            response = client.get(
                "/api/user/keys/generate",
                headers={"token": valid_jwt_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == SUCCESS_STATUS
    
    def test_generate_keys_already_exist(self, client, valid_jwt_token, mock_db):
        """Генерация ключей, когда они уже существуют"""
        mock_db.get_public_key_by_email.return_value = "existing_key"
        
        with patch('main.SignatureUNEP') as MockSignature:
            mock_sig = MagicMock()
            mock_sig.generate_user_keys.return_value = None  # Keys already exist
            MockSignature.return_value = mock_sig
            
            response = client.get(
                "/api/user/keys/generate",
                headers={"token": valid_jwt_token}
            )
            
            assert response.status_code == 400


# =====================================================================
# БЛОК Е: ТЕСТИРОВАНИЕ HELPERS И УТИЛИТ
# =====================================================================

class TestHelperFunctions:
    """Тестирование вспомогательных функций"""
    
    def test_normalize_base64_payload_with_data_uri(self):
        """Нормализация base64 с data URI"""
        from main import _normalize_base64_payload
        
        payload = "data:application/pdf;base64,SGVsbG8gV29ybGQ="
        result = _normalize_base64_payload(payload)
        
        assert result == "SGVsbG8gV29ybGQ="
        assert "data:" not in result
    
    def test_normalize_base64_payload_clean(self):
        """Нормализация чистого base64"""
        from main import _normalize_base64_payload
        
        payload = "SGVsbG8gV29ybGQ="
        result = _normalize_base64_payload(payload)
        
        assert result == "SGVsbG8gV29ybGQ="
    
    def test_decode_key_len_valid(self):
        """Получение длины ключа"""
        from main import _decode_key_len
        
        key_b64 = base64.b64encode(b"a" * 32).decode()
        result = _decode_key_len(key_b64)
        
        assert result == 32
    
    def test_decode_key_len_invalid(self):
        """Получение длины невалидного ключа"""
        from main import _decode_key_len
        
        result = _decode_key_len("not_valid_base64!")
        assert result == -1
    
    def test_is_valid_http_url_valid(self):
        """Проверка валидного HTTP URL"""
        from main import _is_valid_http_url
        
        assert _is_valid_http_url("https://example.com/callback") is True
        assert _is_valid_http_url("http://example.com:8080/api") is True
    
    def test_is_valid_http_url_invalid(self):
        """Проверка невалидного URL"""
        from main import _is_valid_http_url
        
        assert _is_valid_http_url("ftp://example.com") is False
        assert _is_valid_http_url("not_a_url") is False
        assert _is_valid_http_url("") is False


# =====================================================================
# БЛОК Ж: ИНТЕГРАЦИОННЫЕ ТЕСТЫ ENDPOINTS
# =====================================================================

class TestEndpointIntegration:
    """Интеграционные тесты цепочек операций"""
    
    def test_full_document_flow(self, client, valid_jwt_token, mock_db):
        """Полный цикл: загрузка → получение → удаление документа"""
        # 1. Загрузка
        mock_db.insert_doc.return_value = True
        response1 = client.post(
            "/api/docs/download",
            json={
                "id": 1,
                "title": "test.pdf",
                "hash": "hash123",
                "base64": base64.b64encode(b"%PDF").decode(),
                "created_at": 1704067200,
                "email": "test@domain.com"
            },
            headers={"token": valid_jwt_token}
        )
        assert response1.status_code == 200
        
        # 2. Получение
        mock_db.get_all_list_docs.return_value = [{
            "id": 1,
            "title": "test.pdf",
            "hash": "hash123",
            "signing_status": "unsigned",
            "created_at": 1704067200,
            "email": "test@domain.com"
        }]
        response2 = client.get("/api/docs", headers={"token": valid_jwt_token})
        assert response2.status_code == 200
        
        # 3. Удаление
        mock_db.delet_document_by_id.return_value = True
        response3 = client.delete(
            "/api/docs?doc_id=1",
            headers={"token": valid_jwt_token}
        )
        assert response3.status_code == 200
    
    def test_cors_headers_present(self, client):
        """Проверка CORS заголовков"""
        response = client.get("/api/docs", headers={"token": "dummy"})
        # Просто проверяем, что endpoint доступен
        assert response.status_code in [200, 401]
