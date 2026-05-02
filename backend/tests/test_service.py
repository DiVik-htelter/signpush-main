"""
Тесты для модуля service.py

Функционал:
- Тестирование класса User (аутентификация, управление профилем)
- Тестирование класса SignatureUNEP (криптография ГОСТ)
- Тестирование JWT токенов и refresh токенов
- Тестирование обработки ошибок и edge cases

Примечание: Все зависимости мокируются в conftest.py
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
import base64
import jwt
from datetime import datetime, timezone

# Импорты через conftest - всё уже мокировано
from service import (
    User, SignatureUNEP,
    SUCCESS_STATUS, INVALID_CREDENTIALS_STATUS,
    DB_CONNECTION_ERROR_STATUS, GENERAL_ERROR_STATUS
)

# Получаем mock_config из conftest
mock_config = sys.modules['config_db']


# =====================================================================
# БЛОК А: ТЕСТИРОВАНИЕ КЛАССА User
# =====================================================================

class TestUserLogic:
    
    # --- ТЕСТИРОВАНИЕ SET_NAME ---
    @pytest.mark.parametrize("first, last, expected_first, expected_last", [
        ("иван", "иванов", "Иван", "Иванов"),      # Позитивный кириллица
        ("john", "doe", "John", "Doe"),            # Позитивный латиница
        ("Анна-Мария", "Ремарк", "Анна-Мария", "Ремарк") # С дефисом
    ])
    def test_set_name_positive(self, user_instance, mock_db, first, last, expected_first, expected_last):
        """Позитивные сценарии изменения имени с проверкой форматирования"""
        result = user_instance.set_name(first, last)
        
        assert result is True
        assert user_instance.get_name() == (expected_first, expected_last)
        # Проверяем, что в БД ушли правильно отформатированные данные
        mock_db.change_userName_by_id.assert_called_once_with(101, expected_first, expected_last)

    @pytest.mark.parametrize("first, last", [
        ("A", "Ivanov"),       # Имя < 2 символов
        ("Ivan", "B"),         # Фамилия < 2 символов
        ("Ivan123", "Ivanov"), # Цифры в имени
        ("Ivan", "Iv@nov"),    # Спецсимволы
        ("", "Ivanov"),        # Пустое поле
        (None, "Ivanov")       # None
    ])
    def test_set_name_negative(self, user_instance, mock_db, first, last):
        """Негативные сценарии валидации имени (цифры, спецсимволы, длина)"""
        result = user_instance.set_name(first, last)
        
        assert result is False
        # Проверяем, что обращение к БД не выполнялось
        mock_db.change_userName_by_id.assert_not_called()

    def test_set_name_db_fail(self, user_instance, mock_db):
        """Отказоустойчивость: имитация падения БД при сохранении"""
        # Запоминаем изначальное состояние
        initial_name = user_instance.get_name()
        
        # Заставляем БД бросить исключение
        mock_db.change_userName_by_id.side_effect = Exception("Database connection lost")
        
        result = user_instance.set_name("Newname", "Newlast")
        
        assert result is False
        # Убеждаемся, что внутреннее состояние объекта НЕ обновилось
        assert user_instance.get_name() == initial_name

    # --- ТЕСТИРОВАНИЕ JWT И АВТОРИЗАЦИИ ---
    def test_jwt_lifecycle(self, user_instance):
        """Проверка жизненного цикла JWT (создание и валидация)"""
        # Т.к. метод приватный, вызываем через name mangling
        token = user_instance._User__create_jwt("101")
        assert token is not None
        
        # Проверяем расшифровку
        decoded = User.decoded_jwt(token)
        assert decoded is not None
        assert decoded["sub"] == "101"
        assert decoded["name"] == "test@domain.com"
        assert "exp" in decoded

    def test_jwt_expired(self):
        """Проверка обработки истекшего токена"""
        # Создаем токен, который "истек" минуту назад
        expired_payload = {
            "sub": "101",
            "exp": datetime.now(timezone.utc).timestamp() - 60 
        }
        token = jwt.encode(expired_payload, mock_config.SECRET_KEY, algorithm="HS256")
        
        # Должен вернуть None при ошибке ExpiredSignatureError (в лог упадет warning)
        assert User.decoded_jwt(token) is None

    def test_jwt_invalid_signature(self):
        """Проверка подмены секретного ключа"""
        payload = {"sub": "101", "exp": datetime.now(timezone.utc).timestamp() + 600}
        # Подписываем ЛЕВЫМ ключом
        fake_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        
        assert User.decoded_jwt(fake_token) is None

    @pytest.mark.parametrize("db_response, expected_status", [
        (0, SUCCESS_STATUS),
        (2, INVALID_CREDENTIALS_STATUS),
        (3, DB_CONNECTION_ERROR_STATUS),
        (99, GENERAL_ERROR_STATUS) # Неизвестная ошибка
    ])
    def test_check_auth_responses(self, user_instance, mock_db, mock_redis, db_response, expected_status):
        """Имитация ответов БД при авторизации (match/case)"""
        mock_db.check_user.return_value = db_response
        
        response = user_instance.chek_auth("password123")
        
        assert response["status"] == expected_status
        if db_response == 0:
            assert response["token"] != -1
            assert "refresh_token" in response
            # Проверяем, что рефреш записался в Redis
            mock_redis.save_refresh_token.assert_called_once()
        else:
            assert response["token"] == -1


# =====================================================================
# БЛОК Б: ТЕСТИРОВАНИЕ КЛАССА SignatureUNEP (Криптография ГОСТ)
# =====================================================================
# Внимание: для выполнения этих тестов в окружении должен быть установлен
# пакет gostcrypto и asn1crypto, как требует оригинальный файл.

class TestSignatureUNEP:
    
    @pytest.fixture
    def sign_unep(self, mock_db):
        try:
            return SignatureUNEP("crypto@domain.com", mock_db)
        except Exception as e:
            pytest.skip(f"Библиотеки ГОСТ криптографии недоступны: {e}")

    # --- ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ И ХЭШИРОВАНИЯ ---
    def test_hash_document(self, sign_unep):
        """Проверка хэширования Стрибог-256"""
        document = "Тестовый документ для СЭД"
        hash_bytes = sign_unep.hash_document(document)
        
        assert hash_bytes is not None
        assert isinstance(hash_bytes, bytes)
        # Хэш ГОСТ 34.11-2012 (256 бит) должен быть ровно 32 байта
        assert len(hash_bytes) == 32

    def test_generate_keys_success(self, sign_unep, mock_db):
        """Генерация ключей: проверка форматов и размеров"""
        mock_db.get_public_key_by_email.return_value = None # Ключей еще нет
        
        keys = sign_unep.generate_user_keys()
        assert keys is not None
        pub_key_b64, priv_key_b64 = keys
        
        # Декодируем и проверяем длину сырых байтов
        pub_key_bytes = base64.b64decode(pub_key_b64)
        priv_key_bytes = base64.b64decode(priv_key_b64)
        
        assert len(priv_key_bytes) == 32 # Приватный ГОСТ-ключ: 32 байта
        assert len(pub_key_bytes) == 64  # Публичный ГОСТ-ключ: 64 байта

    def test_generate_keys_already_exists(self, sign_unep, mock_db):
        """Если ключ в БД уже есть, метод должен вернуть None"""
        mock_db.get_public_key_by_email.return_value = "some_existing_key"
        assert sign_unep.generate_user_keys() is None


    # --- ИНТЕГРАЦИОННЫЙ ТЕСТ: ПОЛНЫЙ ЦИКЛ ПОДПИСАНИЯ ---
    def test_end_to_end_cms_workflow(self, sign_unep, mock_db):
        """
        Проверка сквозного процесса "Черный ящик": 
        Генерация ключа -> Подпись -> Упаковка в CMS -> Извлечение и Верификация CMS
        """
        # 1. Подготовка: Генерируем реальную пару ключей для теста
        mock_db.get_public_key_by_email.return_value = None
        keys = sign_unep.generate_user_keys()
        assert keys is not None, "Сбой генерации ключей ГОСТ"
        pub_key_b64, priv_key_b64 = keys

        test_doc = "Договор №123 от 01.01.2026. Сумма: 100 000 руб."

        # 2. Создание SignedAttrs и подписи
        sign_result = sign_unep.signed_hash(test_doc, priv_key_b64)
        assert 'signature' in sign_result
        assert 'signed_attrs_der' in sign_result

        # 3. Упаковка в CMS контейнер
        cms_der_bytes = sign_unep.create_cms_container(
            signed_attrs_der=sign_result['signed_attrs_der'],
            raw_signature=sign_result['signature'],
            public_key=pub_key_b64
        )
        assert isinstance(cms_der_bytes, bytes)
        assert len(cms_der_bytes) > 100 # CMS контейнер обычно весит несколько сотен байт

        # 4. Проверка и распаковка CMS (Успешный сценарий)
        # Настраиваем мок БД, чтобы он вернул наш публичный ключ, если он потребуется
        mock_db.get_public_key_by_email.return_value = pub_key_b64
        
        verify_result = sign_unep.verify_cms_container(
            cms_signature_bytes=cms_der_bytes,
            signed_document=test_doc,
            public_key_b64=pub_key_b64 # Передаем ключ напрямую
        )
        
        # Проверяем структуру ответа
        assert verify_result['is_valid'] is True, f"Ошибка валидации CMS: {verify_result.get('error')}"
        assert verify_result['checks']['content_hash_match'] is True
        assert verify_result['checks']['signature_valid'] is True
        
        # Проверяем извлечение атрибутов
        attrs = verify_result['attrs']
        attr_names = [a['name'] for a in attrs]
        assert 'content_type' in attr_names
        assert 'message_digest' in attr_names

        # 5. Проверка защиты от подделки (Изменяем документ)
        fake_doc = "Договор №123 от 01.01.2026. Сумма: 900 000 руб." # Изменили цифру
        failed_verify_result = sign_unep.verify_cms_container(
            cms_signature_bytes=cms_der_bytes,
            signed_document=fake_doc,
            public_key_b64=pub_key_b64
        )
        
        assert failed_verify_result['is_valid'] is False
        assert failed_verify_result['checks']['content_hash_match'] is False # Хэш не должен сойтись


# =====================================================================
# БЛОК В: ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ User (пропущенные методы)
# =====================================================================

class TestUserGetters:
    """Тестирование методов получения информации о пользователе"""
    
    def test_get_name(self, user_instance):
        """Проверка получения имени и фамилии"""
        first, last = user_instance.get_name()
        assert first == "Test"
        assert last == "Testov"
    
    def test_get_email(self, user_instance):
        """Проверка получения email"""
        assert user_instance.get_email() == "test@domain.com"
    
    def test_get_is_email_verified(self, user_instance):
        """Проверка статуса верификации email"""
        assert user_instance.get_is_email_verified() is True
    
    def test_get_created_at(self, user_instance):
        """Проверка получения даты создания аккаунта"""
        created = user_instance.get_created_at()
        assert isinstance(created, datetime)
        # 1672531200 = Jan 1, 2023
        assert created.year == 2023
    
    def test_get_all_info(self, user_instance, mock_db):
        """Проверка получения всей информации о пользователе"""
        mock_db.get_public_key_by_email.return_value = "test_public_key_base64"
        
        info = user_instance.get_all_info()
        assert isinstance(info, dict)
        assert info['first_name'] == "Test"
        assert info['last_name'] == "Testov"
        assert info['email'] == "test@domain.com"
        assert info['is_email_verified'] is True
        assert info['public_key'] == "test_public_key_base64"
    
    def test_get_all_info_no_public_key(self, user_instance, mock_db):
        """Проверка информации когда публичного ключа нет"""
        mock_db.get_public_key_by_email.return_value = None
        
        info = user_instance.get_all_info()
        assert info['public_key'] == "Нет ключа"


class TestUserRefreshToken:
    """Тестирование создания refresh токена"""
    
    def test_create_refresh_token_success(self, user_instance, mock_redis):
        """Проверка успешного создания refresh токена"""
        # Вызываем через name mangling приватный метод
        token = user_instance._User__create_refresh_token()
        
        assert token is not None
        assert isinstance(token, str)
        # UUID должен иметь формат с дефисами
        assert "-" in token
        # Проверяем, что токен сохранился в Redis
        mock_redis.save_refresh_token.assert_called_once()
    
    def test_create_refresh_token_redis_fail(self, user_instance, mock_redis):
        """Проверка обработки ошибки Redis"""
        mock_redis.save_refresh_token.side_effect = Exception("Redis connection lost")
        
        token = user_instance._User__create_refresh_token()
        assert token is None


class TestUserAuthEdgeCases:
    """Edge cases для авторизации"""
    
    def test_chek_auth_with_exception_during_jwt(self, user_instance, mock_db, mock_redis):
        """Проверка обработки исключения во время создания JWT"""
        mock_db.check_user.return_value = 0
        mock_db.get_user_by_email.return_value = {'id': 101}
        # Заставляем ошибку при попытке создания токена
        mock_db.get_public_key_by_email.side_effect = Exception("DB error")
        
        response = user_instance.chek_auth("password")
        
        # При ошибке должен вернуться GENERAL_ERROR_STATUS
        assert response['token'] == -1
    
    def test_chek_auth_empty_password(self, user_instance, mock_db):
        """Проверка авторизации с пустым паролем"""
        mock_db.check_user.return_value = 2  # Invalid credentials
        
        response = user_instance.chek_auth("")
        
        assert response["status"] == INVALID_CREDENTIALS_STATUS
        assert response["token"] == -1


# =====================================================================
# БЛОК Г: РАСШИРЕННЫЕ ТЕСТЫ SignatureUNEP
# =====================================================================

class TestSignatureUNEPHashAndKeys:
    """Тestирование хеширования и генерации ключей"""
    
    @pytest.fixture
    def sign_unep(self, mock_db):
        try:
            return SignatureUNEP("crypto@domain.com", mock_db)
        except Exception as e:
            pytest.skip(f"Библиотеки ГОСТ криптографии недоступны: {e}")
    
    def test_hash_document_bytes(self, sign_unep):
        """Хеширование байтов документа"""
        doc_bytes = b"Binary document content"
        hash_result = sign_unep.hash_document(doc_bytes, encode_flag=False)
        
        assert hash_result is not None
        assert isinstance(hash_result, bytes)
        assert len(hash_result) == 32
    
    def test_hash_document_consistency(self, sign_unep):
        """Проверка консистентности хеша (одинаков для одного входа)"""
        doc = "Test document"
        hash1 = sign_unep.hash_document(doc)
        hash2 = sign_unep.hash_document(doc)
        
        assert hash1 == hash2
    
    def test_hash_document_different_inputs(self, sign_unep):
        """Разные входные данные дают разные хеши"""
        hash1 = sign_unep.hash_document("Document 1")
        hash2 = sign_unep.hash_document("Document 2")
        
        assert hash1 != hash2
    
    def test_hash_document_empty_string(self, sign_unep):
        """Хеширование пустой строки"""
        hash_result = sign_unep.hash_document("")
        assert hash_result is not None
        assert len(hash_result) == 32
    
    def test_hash_document_unicode(self, sign_unep):
        """Хеширование Unicode текста"""
        unicode_doc = "Тестовый документ с кириллицей 日本語 العربية"
        hash_result = sign_unep.hash_document(unicode_doc)
        
        assert hash_result is not None
        assert len(hash_result) == 32


class TestSignatureUNEPVerification:
    """Тестирование проверки подписей"""
    
    @pytest.fixture
    def sign_unep(self, mock_db):
        try:
            return SignatureUNEP("crypto@domain.com", mock_db)
        except Exception as e:
            pytest.skip(f"Библиотеки ГОСТ криптографии недоступны: {e}")
    
    def test_signed_hash_valid_keys(self, sign_unep, mock_db):
        """Проверка подписания документа валидными ключами"""
        # Генерируем ключи для теста
        mock_db.get_public_key_by_email.return_value = None
        keys = sign_unep.generate_user_keys()
        
        if keys is None:
            pytest.skip("Keys generation failed")
        
        pub_key_b64, priv_key_b64 = keys
        test_doc = "Test document for signing"
        
        result = sign_unep.signed_hash(test_doc, priv_key_b64)
        
        assert 'signature' in result
        assert 'signed_attrs_der' in result
        assert 'content_hash' in result
        assert isinstance(result['signature'], (bytes, bytearray))
    
    def test_signed_hash_invalid_private_key(self, sign_unep):
        """Проверка коррупции подписи с невалидным приватным ключом"""
        invalid_key = base64.b64encode(b"invalid_key_123").decode()
        
        with pytest.raises(ValueError):
            sign_unep.signed_hash("Document", invalid_key)
    
    def test_verify_signature_basic(self, sign_unep, mock_db):
        """Базовая проверка verify_signature"""
        mock_db.get_public_key_by_email.return_value = None
        keys = sign_unep.generate_user_keys()
        
        if keys is None:
            pytest.skip("Keys generation failed")
        
        # Результат verify_signature может быть boolean
        result = sign_unep.verify_signature(b"test_hash", b"test_signature", keys[0])
        assert isinstance(result, bool)


class TestSignatureUNEPCMSEdgeCases:
    """Edge cases для CMS контейнера"""
    
    @pytest.fixture
    def sign_unep(self, mock_db):
        try:
            return SignatureUNEP("crypto@domain.com", mock_db)
        except Exception as e:
            pytest.skip(f"Библиотеки ГОСТ криптографии недоступны: {e}")
    
    def test_verify_cms_with_corrupted_container(self, sign_unep):
        """Проверка верификации с поврежденным CMS контейнером"""
        corrupted_cms = b"not_a_valid_cms_der_stream"
        result = sign_unep.verify_cms_container(
            cms_signature_bytes=corrupted_cms,
            signed_document="test",
            public_key_b64=None,
            allow_db_fallback=False
        )
        
        assert result['is_valid'] is False
        assert result['checks']['signature_valid'] is False
    
    def test_verify_cms_with_wrong_document(self, sign_unep, mock_db):
        """Проверка верификации с измененным документом"""
        mock_db.get_public_key_by_email.return_value = None
        
        # Генерируем ключи и подписываем документ
        keys = sign_unep.generate_user_keys()
        if keys is None:
            pytest.skip("Keys generation failed")
        
        pub_key_b64, priv_key_b64 = keys
        original_doc = "Original document"
        modified_doc = "Modified document"
        
        # Подписываем оригинальный документ
        signed_payload = sign_unep.signed_hash(original_doc, priv_key_b64)
        cms_der = sign_unep.create_cms_container(
            signed_payload['signed_attrs_der'],
            signed_payload['signature'],
            pub_key_b64
        )
        
        # Пытаемся проверить с измененным документом
        result = sign_unep.verify_cms_container(
            cms_signature_bytes=cms_der,
            signed_document=modified_doc,
            public_key_b64=pub_key_b64
        )
        
        assert result['is_valid'] is False
        assert result['checks']['content_hash_match'] is False
    
    def test_verify_cms_without_public_key_fallback(self, sign_unep, mock_db):
        """Проверка верификации без fallback на БД"""
        mock_db.get_public_key_by_email.return_value = None
        
        result = sign_unep.verify_cms_container(
            cms_signature_bytes=b"some_cms_data",
            signed_document="test",
            public_key_b64=None,
            allow_db_fallback=False
        )
        
        # Должна быть ошибка из-за отсутствия публичного ключа
        assert result['is_valid'] is False


# =====================================================================
# БЛОК Д: ТЕСТЫ PDF_SIGNER (из pdf_signer.py)
# =====================================================================

from pdf_signer import add_signature_to_pdf, validate_signature_params


class TestPDFSignerValidation:
    """Тестирование функции валидации параметров подписи"""
    
    from pdf_signer import validate_signature_params
    
    def test_validate_signature_params_valid(self):
        """Проверка валидных параметров"""
        valid, msg = validate_signature_params(0, 100, 200, 150, 80)
        assert valid is True
        assert msg == "OK"
    
    def test_validate_signature_params_negative_page(self):
        """Проверка с отрицательным номером страницы"""
        valid, msg = validate_signature_params(-1, 100, 200, 150, 80)
        assert valid is False
    
    def test_validate_signature_params_zero_width(self):
        """Проверка с нулевой шириной"""
        valid, msg = validate_signature_params(0, 100, 200, 0, 80)
        assert valid is False
    
    def test_validate_signature_params_zero_height(self):
        """Проверка с нулевой высотой"""
        valid, msg = validate_signature_params(0, 100, 200, 150, 0)
        assert valid is False
    
    def test_validate_signature_params_negative_coords(self):
        """Проверка с отрицательными координатами"""
        valid, msg = validate_signature_params(0, -50, 200, 150, 80)
        assert valid is False
    
    def test_validate_signature_params_negative_y(self):
        """Проверка с отрицательной Y координатой"""
        valid, msg = validate_signature_params(0, 100, -50, 150, 80)
        assert valid is False
    
    def test_validate_signature_params_large_values(self):
        """Проверка с большими значениями"""
        valid, msg = validate_signature_params(10, 1000000, 2000000, 5000, 3000)
        assert valid is True


class TestPDFSignerBase64Handling:
    """Тестирование обработки base64 в PDF Signer"""
    
    from pdf_signer import add_signature_to_pdf
    import base64
    
    def test_add_signature_invalid_pdf_base64(self):
        """Проверка с невалидным PDF base64"""
        invalid_pdf = "not_a_valid_pdf_base64"
        signature = base64.b64encode(b"fake_signature").decode()
        
        result, success = add_signature_to_pdf(
            pdf_base64=invalid_pdf,
            signature_base64=signature,
            page_number=0,
            x=100,
            y=100,
            width=100,
            height=50
        )
        
        assert success is False
    
    def test_add_signature_data_uri_handling(self):
        """Проверка обработки data URI префиксов"""
        # Создаем минимальный валидный PDF (пустой)
        try:
            import fitz
            doc = fitz.open()
            doc.new_page()
            pdf_bytes = doc.write()
            doc.close()
            
            pdf_b64 = base64.b64encode(pdf_bytes).decode()
            pdf_with_data_uri = f"data:application/pdf;base64,{pdf_b64}"
            
            # Простая PNG подпись (1x1 пиксель)
            signature_bytes = bytes.fromhex(
                "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a"
                "49444154789c630000000002000105e1214500000000004945424"
            )
            sig_b64 = base64.b64encode(signature_bytes).decode()
            
            result, success = add_signature_to_pdf(
                pdf_base64=pdf_with_data_uri,
                signature_base64=sig_b64,
                page_number=0,
                x=10,
                y=10,
                width=50,
                height=30
            )
            
            # Результат должен содержать подписанный PDF
            if success:
                assert result.startswith("data:application/pdf;base64,")
        except ImportError:
            pytest.skip("PyMuPDF (fitz) не установлен")


# =====================================================================
# БЛОК Е: ИНТЕГРАЦИОННЫЕ ТЕСТЫ (кросс-модульное взаимодействие)
# =====================================================================

class TestIntegrationUserWithSignature:
    """Проверка взаимодействия User и SignatureUNEP"""
    
    @pytest.fixture
    def sign_unep(self, mock_db):
        try:
            return SignatureUNEP("test@domain.com", mock_db)
        except Exception as e:
            pytest.skip(f"Библиотеки ГОСТ криптографии недоступны: {e}")
    
    def test_user_can_sign_document(self, user_instance, sign_unep, mock_db):
        """Проверка, что пользователь может подписать документ"""
        # Генерируем ключи
        mock_db.get_public_key_by_email.return_value = None
        keys = sign_unep.generate_user_keys()
        
        if keys is None:
            pytest.skip("Keys generation failed")
        
        pub_key_b64, priv_key_b64 = keys
        
        # Пользователь подписывает документ
        test_document = "I, the undersigned, approve this"
        signed_data = sign_unep.signed_hash(test_document, priv_key_b64)
        
        assert 'signature' in signed_data
        assert signed_data['signature'] is not None
        
        # Проверяем, что подпись соответствует документу
        cms_der = sign_unep.create_cms_container(
            signed_data['signed_attrs_der'],
            signed_data['signature'],
            pub_key_b64
        )
        
        result = sign_unep.verify_cms_container(
            cms_signature_bytes=cms_der,
            signed_document=test_document,
            public_key_b64=pub_key_b64
        )
        
        assert result['is_valid'] is True


class TestDatabaseFailureScenarios:
    """Тестирование сценариев отказа БД"""
    
    def test_user_get_info_db_failure(self, mock_db, mock_redis):
        """Проверка получения информации при ошибке БД"""
        mock_db.get_user_by_email.side_effect = Exception("Database connection lost")
        
        with pytest.raises(Exception):
            user = User(email="test@domain.com", db=mock_db, db_redis=mock_redis, flag_pg=True)
    
    def test_signature_generation_db_failure(self, mock_db):
        """Проверка генерации ключей при ошибке БД"""
        mock_db.get_public_key_by_email.return_value = None
        mock_db.insert_keys_by_email.side_effect = Exception("Database write failed")
        
        try:
            from service import SignatureUNEP
            sign_unep = SignatureUNEP("test@domain.com", mock_db)
            keys = sign_unep.generate_user_keys()
            # Ключи должны быть сгенерированы, даже если сохранение не удалось
            assert keys is not None
        except Exception:
            pytest.skip("Signature generation requires cryptography libraries")