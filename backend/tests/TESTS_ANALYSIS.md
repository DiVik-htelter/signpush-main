# Анализ тестов проекта SignPush

## Оглавление
1. [Обзор структуры тестов](#обзор-структуры-тестов)
2. [test_api_endpoints.py](#test_api_endpointspy)
3. [test_database.py](#test_databasepy)
4. [test_service.py](#test_servicepy)
5. [conftest.py](#confestpy)

---

## Обзор структуры тестов

Проект содержит **4 основных файла** с тестами:
- `conftest.py` - глобальная конфигурация фиксстур
- `test_api_endpoints.py` - REST API тесты (781 строка)
- `test_database.py` - тесты БД операций (351 строка)
- `test_service.py` - тесты бизнес-логики (692 строка)

**Всего тест-классов:** 20+
**Всего тестов:** 100+

---

# test_api_endpoints.py

## Блок А: Тестирование аутентификации

### Класс: `TestAuthentication`
Тестирует функцию `check_token()` - парсинг и валидация JWT токенов.

#### test_check_token_valid
- **Вход:** Валидный JWT токен
- **Выход:** Email пользователя ("test@domain.com")
- **Поведение:** Функция должна декодировать токен и вернуть email из поля `name`

#### test_check_token_invalid
- **Вход:** Невалидная строка "invalid.token.not.valid"
- **Выход:** False
- **Поведение:** При ошибке парсинга вернуть False

#### test_check_token_expired
- **Вход:** Токен с `exp` в прошлом (истек 60 сек назад)
- **Выход:** False или None
- **Поведение:** При истечении срока вернуть False

#### test_check_token_none
- **Вход:** None
- **Выход:** False
- **Поведение:** Обработка None без ошибок

#### test_check_token_empty_string
- **Вход:** Пустая строка ""
- **Выход:** False
- **Поведение:** Обработка пустой строки без ошибок

---

### Класс: `TestAuthEndpoint`
Тестирует endpoint `POST /api/auth/` - аутентификация пользователя.

#### test_auth_success
- **Вход:** 
  - JSON: `{"mail": "test@domain.com", "password": "password123"}`
  - `mock_db.check_user.return_value = 0` (успех)
  - `mock_db.get_user_by_email()` возвращает информацию пользователя
- **Выход:** HTTP 200, JSON с `status=SUCCESS_STATUS`, содержит `token` и `refresh_token`
- **Поведение:** 
  - Вызвать `User.chek_auth()` с паролем
  - При кодe 0 (успех) вернуть токены

#### test_auth_invalid_credentials
- **Вход:** 
  - `mock_db.check_user.return_value = 2` (неверные данные)
- **Выход:** HTTP 200, JSON с `status=INVALID_CREDENTIALS_STATUS`, `token=-1`
- **Поведение:** Вернуть статус ошибки без токена

#### test_auth_db_error
- **Вход:** 
  - `mock_db.check_user.return_value = 3` (ошибка БД)
- **Выход:** HTTP 200, JSON с `status=DB_CONNECTION_ERROR_STATUS`, `token=-1`
- **Поведение:** Вернуть статус ошибки подключения к БД

---

## Блок Б: Тестирование работы с документами

### Класс: `TestDocumentEndpoints`
Тестирует endpoints для работы с документами.

#### test_get_docs_unauthorized
- **Вход:** GET /api/docs без токена
- **Выход:** HTTP 401
- **Поведение:** Обязательное требование токена

#### test_get_docs_with_valid_jwt_token
- **Вход:** 
  - GET /api/docs с валидным токеном
  - `mock_db.get_all_list_docs()` возвращает список из 1 документа
- **Выход:** HTTP 200, JSON с сообщением "There are 1 paperes", массив документов
- **Поведение:** Вернуть список документов пользователя

#### test_get_docs_by_id_success
- **Вход:** 
  - PATCH /api/docs?doc_id=1 с токеном
  - `mock_db.get_document_by_id(1)` возвращает документ
- **Выход:** HTTP 200
- **Поведение:** Вернуть информацию о документе

#### test_get_docs_by_id_not_found
- **Вход:** 
  - PATCH /api/docs?doc_id=999 с токеном
  - `mock_db.get_document_by_id(999)` возвращает None
- **Выход:** HTTP 404
- **Поведение:** Вернуть 404 когда документа не существует

#### test_delete_document_success
- **Вход:** 
  - DELETE /api/docs?doc_id=1 с токеном
  - `mock_db.delet_document_by_id()` возвращает True
- **Выход:** HTTP 200, JSON с `success=True`
- **Поведение:** Успешно удалить документ

#### test_delete_document_failure
- **Вход:** 
  - DELETE /api/docs?doc_id=999 с токеном
  - `mock_db.delet_document_by_id()` возвращает False
- **Выход:** HTTP 200, JSON с `success=False`
- **Поведение:** Вернуть false когда удаление не удалось

#### test_download_document
- **Вход:** 
  - GET /api/docs/download/?doc_id=1 с токеном
  - PDF содержимое в base64
- **Выход:** HTTP 200, бинарное содержимое PDF
- **Поведение:** Декодировать base64 и вернуть содержимое

---

### Класс: `TestDocumentUpload`
Тестирует загрузку документов.

#### test_insert_doc_success
- **Вход:** 
  - POST /api/docs/download с JSON содержащим document data в base64
  - `mock_db.insert_doc()` возвращает True
  - Требуется токен
- **Выход:** HTTP 200, JSON с `success=True`
- **Поведение:** Сохранить документ в БД

#### test_insert_doc_unauthorized
- **Вход:** 
  - POST /api/docs/download БЕЗ токена
- **Выход:** HTTP 401
- **Поведение:** Требовать токен для загрузки

---

## Блок В: Тестирование подписей

### Класс: `TestSignatureEndpoints`
Тестирует подписание документов.

#### test_sign_document_no_token
- **Вход:** POST /api/document/sign/ без токена
- **Выход:** HTTP 401
- **Поведение:** Требовать токен

#### test_sign_document_invalid_params
- **Вход:** 
  - JSON с `width=-50` (отрицательное значение)
  - Остальные параметры валидны
- **Выход:** HTTP 400
- **Поведение:** Валидировать параметры (width, height должны быть > 0)

#### test_sign_document_not_found
- **Вход:** 
  - `document_id=999` когда документа не существует
  - `mock_db.get_document_by_id()` возвращает None
- **Выход:** HTTP 404
- **Поведение:** Вернуть 404 если документ не найден

---

### Класс: `TestUNEPSignatureEndpoints`
Тестирует УНЭП (GOST) подписи.

#### test_sign_unep_unauthorized
- **Вход:** POST /api/document/sign/unep/ без токена
- **Выход:** HTTP 401
- **Поведение:** Требовать токен

#### test_verify_unep_unauthorized
- **Вход:** POST /api/document/verify/unep/ без токена
- **Выход:** HTTP 401
- **Поведение:** Требовать токен

#### test_verify_unep_invalid_signature
- **Вход:** 
  - `mock_sig.verify_cms_container()` возвращает `is_valid=False`
- **Выход:** HTTP 200, JSON с `is_valid=False`
- **Поведение:** Вернуть результат проверки подписи

---

## Блок Г: Тестирование пользователя

### Класс: `TestUserInfoEndpoints`
Тестирует endpoints информации о пользователе.

#### test_get_user_info_unauthorized
- **Вход:** GET /api/user/info без токена
- **Выход:** HTTP 401
- **Поведение:** Требовать токен

#### test_get_user_info_success
- **Вход:** 
  - GET /api/user/info с валидным токеном
  - `mock_db.get_user_by_email()` и `get_public_key_by_email()` возвращают данные
- **Выход:** HTTP 200
- **Поведение:** Вернуть информацию о пользователе включая публичный ключ

#### test_update_user_info_success
- **Вход:** 
  - POST /api/user/info/update с JSON
  - `first_name`, `last_name`, `new_password`
  - `mock_user.set_name()` возвращает True
- **Выход:** HTTP 200, JSON с `status=SUCCESS_STATUS`
- **Поведение:** Успешно обновить информацию

#### test_update_user_info_invalid
- **Вход:** 
  - `first_name="J"` (слишком короткое, < 2 символов)
  - `mock_user.set_name()` возвращает False
- **Выход:** HTTP 200, JSON с `status=GENERAL_ERROR_STATUS`
- **Поведение:** Валидировать длину имени

---

### Класс: `TestUserRegistration`
Тестирует регистрацию.

#### test_register_user_success
- **Вход:** 
  - POST /api/register/ с email, password, first_name, last_name
  - `mock_db.insert_user()` возвращает True
- **Выход:** HTTP 200, JSON с `status=SUCCESS_STATUS`
- **Поведение:** Создать нового пользователя

#### test_register_user_duplicate_email
- **Вход:** 
  - Email который уже существует
  - `mock_db.insert_user()` возвращает False
- **Выход:** HTTP 200, статус != SUCCESS_STATUS
- **Поведение:** Не позволить дубликаты email

---

## Блок Д: Тестирование внешних сервисов

### Класс: `TestExternalServiceAPI`
Интеграция с внешними сервисами (например, 1C).

#### test_register_via_external_api
- **Вход:** 
  - POST /api/v1/user/register с внешних сервисов
- **Выход:** HTTP 200, JSON со статусом
- **Поведение:** Регистрировать пользователя через внешний API

#### test_document_validation_hash_mismatch
- **Вход:** 
  - hash документа не совпадает с SHA256(base64_content)
  - POST /api/v1/document/sign/unep
- **Выход:** HTTP 400, JSON с `success=False`
- **Поведение:** Валидировать целостность документа через хеш

#### test_external_webhook_return
- **Вход:** 
  - POST /api/v1/document/webhook с документом и callback URL
  - `send_signed_doc()` имитируется (AsyncMock)
- **Выход:** HTTP 200, JSON с `success=True`
- **Поведение:** Отправить подписанный документ на webhook

---

## Блок E: Тестирование генерации ключей

### Класс: `TestKeyGeneration`
Управление криптографическими ключами.

#### test_generate_keys_success
- **Вход:** 
  - GET /api/user/keys/generate с токеном
  - `mock_db.get_public_key_by_email()` возвращает None (нет ключей)
  - `mock_sig.generate_user_keys()` возвращает (pub, priv)
- **Выход:** HTTP 200, JSON с `status=SUCCESS_STATUS`
- **Поведение:** Создать пару ключей GOST и сохранить в БД

#### test_generate_keys_already_exist
- **Вход:** 
  - Публичный ключ уже существует в БД
  - `mock_sig.generate_user_keys()` возвращает None
- **Выход:** HTTP 400
- **Поведение:** Не переписывать существующие ключи

---

## Блок Ж: Тестирование вспомогательных функций

### Класс: `TestHelperFunctions`
Утилиты для обработки данных.

#### test_normalize_base64_payload_with_data_uri
- **Вход:** "data:application/pdf;base64,SGVsbG8gV29ybGQ="
- **Выход:** "SGVsbG8gV29ybGQ="
- **Поведение:** Удалить префикс data URI

#### test_normalize_base64_payload_clean
- **Вход:** "SGVsbG8gV29ybGQ="
- **Выход:** "SGVsbG8gV29ybGQ=" (без изменений)
- **Поведение:** Оставить чистый base64 как есть

#### test_decode_key_len_valid
- **Вход:** Base64 строка ключа длины 32 байта
- **Выход:** 32
- **Поведение:** Вернуть длину декодированного ключа

#### test_decode_key_len_invalid
- **Вход:** "not_valid_base64!"
- **Выход:** -1
- **Поведение:** Вернуть -1 при ошибке декодирования

#### test_is_valid_http_url_valid
- **Вход:** "https://example.com/callback" или "http://example.com:8080/api"
- **Выход:** True
- **Поведение:** Валидировать HTTP/HTTPS URL

#### test_is_valid_http_url_invalid
- **Вход:** "ftp://example.com", "not_a_url", ""
- **Выход:** False
- **Поведение:** Отклонить неправильные URL

---

## Блок И: Интеграционные тесты API

### Класс: `TestEndpointIntegration`
Цепочки связанных операций.

#### test_full_document_flow
- **Вход:** Последовательно:
  1. Загрузка документа POST /api/docs/download
  2. Получение списка GET /api/docs
  3. Удаление DELETE /api/docs?doc_id=1
- **Выход:** Все операции HTTP 200
- **Поведение:** Полный жизненный цикл документа

#### test_cors_headers_present
- **Вход:** GET /api/docs с dummy токеном
- **Выход:** HTTP 200 или 401 (наличие ответа)
- **Поведение:** Проверить поддержу CORS

---

# test_database.py

## Блок А: Операции с пользователями

### Класс: `TestDatabaseUserOperations`
CRUD операции с пользователями в PostgreSQL.

#### test_insert_user_success
- **Вход:** 
  - `email="test@domain.com"`
  - `password="hashed_pass"`
  - `name={'firstName': 'John', 'lastName': 'Doe'}`
  - `mock_postgres_cursor.fetchone()` возвращает (1,) - ID
- **Выход:** Cursor.execute() была вызвана
- **Поведение:** Вставить нового пользователя в DB.users

#### test_insert_user_duplicate_email
- **Вход:** 
  - Email который уже существует
  - `mock_cursor.execute.side_effect = Exception("UNIQUE constraint violated")`
- **Выход:** Исключение Exception
- **Поведение:** Таблица имеет UNIQUE constraint на email

#### test_get_user_by_email
- **Вход:** 
  - `email="test@domain.com"`
  - `mock_cursor.fetchone()` возвращает (1, 'John', 'Doe', 'test@domain.com', True, 1704067200)
- **Выход:** Словарь или кортеж с данными пользователя
- **Поведение:** SELECT где email = ?

#### test_get_user_by_email_not_found
- **Вход:** 
  - Несуществующий email
  - `mock_cursor.fetchone()` возвращает None
- **Выход:** None или пустое значение
- **Поведение:** Вернуть None если не найден

#### test_check_user_valid_credentials
- **Вход:** 
  - `email="test@domain.com"`, `password="password123"`
  - `mock_cursor.fetchone()` возвращает (0,) - код успеха
- **Выход:** 0
- **Поведение:** Проверить пароль через хеш в БД

#### test_check_user_invalid_credentials
- **Вход:** 
  - `mock_cursor.fetchone()` возвращает (2,) - неверный пароль
- **Выход:** 2
- **Поведение:** Вернуть код ошибки

#### test_is_original_email_available
- **Вход:** 
  - `email="available@domain.com"`
  - `mock_cursor.fetchone()` возвращает (0,) - no results
- **Выход:** True или 0
- **Поведение:** Email доступен для регистрации

#### test_is_original_email_taken
- **Вход:** 
  - `mock_cursor.fetchone()` возвращает (1,) - email существует
- **Выход:** False или 1
- **Поведение:** Email уже занят

#### test_change_userName_by_id
- **Вход:** 
  - `user_id=1`, `first_name="Jane"`, `last_name="Smith"`
- **Выход:** Cursor.execute() была вызвана
- **Поведение:** UPDATE пользователя по ID

---

## Блок Б: Операции с документами

### Класс: `TestDatabaseDocumentOperations`
Управление документами в PostgreSQL.

#### test_insert_doc_success
- **Вход:** 
  - `title="test.pdf"`
  - `hash="abc123"` (SHA256)
  - `created_at=1704067200` (timestamp)
  - `base64="base64content"`
  - `email="test@domain.com"`
- **Выход:** Cursor.execute() вызвана
- **Поведение:** INSERT в таблицу документов

#### test_get_document_by_id
- **Вход:** 
  - `doc_id=1`
  - `mock_cursor.fetchone()` возвращает (1, 'test.pdf', 'abc123', 'base64', 'test@domain.com')
- **Выход:** Словарь документа
- **Поведение:** SELECT документа по ID

#### test_get_document_by_id_not_found
- **Вход:** 
  - `doc_id=999`
  - `mock_cursor.fetchone()` возвращает None
- **Выход:** None
- **Поведение:** Вернуть None если не найден

#### test_get_all_list_docs
- **Вход:** 
  - `email="test@domain.com"`
  - `mock_cursor.fetchall()` возвращает список из 2 документов
- **Выход:** Список с 2 элементами
- **Поведение:** SELECT все документы WHERE email = ?

#### test_get_all_list_docs_empty
- **Вход:** 
  - `email="noissue@domain.com"` (нет документов)
  - `mock_cursor.fetchall()` возвращает []
- **Выход:** Пустой список []
- **Поведение:** Вернуть пустой список если нет документов

#### test_delet_document_by_id_success
- **Вход:** 
  - `doc_id=1`
  - `mock_cursor.rowcount=1` (1 строка удалена)
- **Выход:** Успех
- **Поведение:** DELETE документа

#### test_delet_document_by_id_not_found
- **Вход:** 
  - `doc_id=999` (не существует)
  - `mock_cursor.rowcount=0`
- **Выход:** Успех (но ничего не удалено)
- **Поведение:** Не ошибка если документа нет

#### test_insert_signed_document
- **Вход:** 
  - Подписанный документ с координатами подписи
  - `signature_data={'x': 100, 'y': 100, 'width': 50, 'height': 50}`
  - `original_doc_id=1`
  - `signer="test@domain.com"`
- **Выход:** Cursor.execute() вызвана
- **Поведение:** INSERT подписанного документа с метаданными

---

## Блок В: Операции с криптографическими ключами

### Класс: `TestDatabaseKeyOperations`
Управление ключами GOST.

#### test_insert_keys_by_email
- **Вход:** 
  - `email="test@domain.com"`
  - `public_key="pub_key_b64"` (base64 encoded)
  - `private_key="priv_key_b64"` (base64 encoded)
- **Выход:** Cursor.execute() вызвана
- **Поведение:** INSERT в таблицу ключей

#### test_get_public_key_by_email
- **Вход:** 
  - `email="test@domain.com"`
  - `mock_cursor.fetchone()` возвращает ("pub_key_b64",)
- **Выход:** "pub_key_b64"
- **Поведение:** SELECT публичный ключ

#### test_get_public_key_by_email_not_found
- **Вход:** 
  - `mock_cursor.fetchone()` возвращает None
- **Выход:** None
- **Поведение:** Нет публичного ключа

#### test_get_private_key_by_email
- **Вход:** 
  - `email="test@domain.com"`
  - `mock_cursor.fetchone()` возвращает ("priv_key_b64",)
- **Выход:** "priv_key_b64"
- **Поведение:** SELECT приватный ключ (ВНИМАНИЕ: должна быть защита!)

#### test_get_private_key_by_email_not_found
- **Вход:** 
  - `mock_cursor.fetchone()` возвращает None
- **Выход:** None
- **Поведение:** Нет приватного ключа

---

## Блок Г: Операции с Redis

### Класс: `TestDatabaseRedisOperations`
Кэширование токенов в Redis.

#### test_save_refresh_token
- **Вход:** 
  - `email="test@domain.com"`
  - `refresh_token="refresh_token_123"`
- **Выход:** Cursor.setex() вызвана
- **Поведение:** Сохранить токен с TTL

#### test_get_refresh_token
- **Вход:** 
  - `email="test@domain.com"`
  - `mock_redis.get()` возвращает b"refresh_token_123"
- **Выход:** "refresh_token_123" (декодированный)
- **Поведение:** Получить токен из кэша

#### test_get_refresh_token_expired
- **Вход:** 
  - `mock_redis.get()` возвращает None (истек)
- **Выход:** None
- **Поведение:** TTL истек, ключ удален

#### test_delete_refresh_token
- **Вход:** 
  - `email="test@domain.com"`
  - `mock_redis.delete()` возвращает 1
- **Выход:** Успех
- **Поведение:** Удалить токен из кэша (logout)

---

## Блок Д: Интеграционные тесты БД

### Класс: `TestDatabaseIntegration`
Полные жизненные циклы.

#### test_full_user_lifecycle
- **Вход:** Последовательно:
  1. `insert_user(email, password, name)`
  2. `get_user_by_email(email)`
  3. `change_userName_by_id(id, new_first, new_last)`
- **Выход:** Все операции успешны
- **Поведение:** От регистрации до обновления профиля

#### test_full_document_lifecycle
- **Вход:** Последовательно:
  1. `insert_doc(title, hash, created_at, base64, email)`
  2. `get_document_by_id(id)`
  3. `delet_document_by_id(id)`
- **Выход:** Все операции успешны
- **Поведение:** От загрузки до удаления

---

# test_service.py

## Блок А: Логика класса User

### Класс: `TestUserLogic`
Тестирование основных методов User.

#### test_set_name_positive
- **Вход (параметризированный):**
  - ("иван", "иванов") → Expected ("Иван", "Иванов")
  - ("john", "doe") → Expected ("John", "Doe")
  - ("Анна-Мария", "Ремарк") → Expected (с дефисом)
- **Выход:** True, имя изменено
- **Поведение:** Капитализировать имя и фамилию, сохранить в БД

#### test_set_name_negative (параметризированный)
- **Вход (невалидные):**
  - ("A", "Ivanov") - имя < 2 символов
  - ("Ivan", "B") - фамилия < 2 символов
  - ("Ivan123", "Ivanov") - цифры в имени
  - ("Ivan", "Iv@nov") - спецсимволы
  - ("", "Ivanov") - пустое поле
  - (None, "Ivanov") - None
- **Выход:** False
- **Поведение:** Валидировать формат, не сохранять в БД

#### test_set_name_db_fail
- **Вход:** 
  - `mock_db.change_userName_by_id.side_effect = Exception("Database connection lost")`
  - Вызов `set_name("Newname", "Newlast")`
- **Выход:** False
- **Поведение:** Обработать исключение, вернуть False, не изменить внутреннее состояние

---

#### test_jwt_lifecycle
- **Вход:** 
  - Вызвать приватный метод `_User__create_jwt("101")`
  - Затем `User.decoded_jwt(token)`
- **Выход:** `decoded["sub"]="101"`, `decoded["name"]="test@domain.com"`, exists `exp`
- **Поведение:** JWT должен содержать sub, name, exp с правильными значениями

#### test_jwt_expired
- **Вход:** 
  - Токен с `exp` = текущее время - 60 сек
- **Выход:** None
- **Поведение:** ExpiredSignatureError → None (логируется)

#### test_jwt_invalid_signature
- **Вход:** 
  - JWT подписан с неправильным secret key
- **Выход:** None
- **Поведение:** InvalidSignatureError → None

#### test_check_auth_responses (параметризированный)
- **Вход (матрица):**
  - DB возвращает 0 → expected STATUS=SUCCESS, token != -1
  - DB возвращает 2 → expected STATUS=INVALID_CREDENTIALS, token=-1
  - DB возвращает 3 → expected STATUS=DB_CONNECTION_ERROR, token=-1
  - DB возвращает 99 → expected STATUS=GENERAL_ERROR, token=-1
- **Выход:** Соответствующий статус в ответе
- **Поведение:** match/case по коду ошибки БД

---

### Класс: `TestUserGetters`
Методы получения информации.

#### test_get_name
- **Вход:** `user_instance.get_name()`
- **Выход:** ("Test", "Testov")
- **Поведение:** Вернуть кортеж (first_name, last_name)

#### test_get_email
- **Вход:** `user_instance.get_email()`
- **Выход:** "test@domain.com"
- **Поведение:** Вернуть email

#### test_get_is_email_verified
- **Вход:** `user_instance.get_is_email_verified()`
- **Выход:** True
- **Поведение:** Вернуть флаг верификации

#### test_get_created_at
- **Вход:** `user_instance.get_created_at()`
- **Выход:** datetime объект за 2023-01-01
- **Поведение:** Конвертировать timestamp в datetime

#### test_get_all_info
- **Вход:** 
  - `mock_db.get_public_key_by_email()` возвращает "test_public_key_base64"
  - Вызов `get_all_info()`
- **Выход:** Словарь с all user info + public_key
- **Поведение:** Аггрегировать все данные пользователя

#### test_get_all_info_no_public_key
- **Вход:** 
  - Публичного ключа нет
  - `mock_db.get_public_key_by_email()` возвращает None
- **Выход:** info['public_key'] = "Нет ключа"
- **Поведение:** Обработать отсутствие ключа

---

### Класс: `TestUserRefreshToken`
Создание refresh токенов.

#### test_create_refresh_token_success
- **Вход:** 
  - Вызов `_User__create_refresh_token()` (name mangling)
- **Выход:** UUID строка с дефисами
- **Поведение:** 
  - Сгенерировать UUID
  - Сохранить в Redis
  - Вернуть токен

#### test_create_refresh_token_redis_fail
- **Вход:** 
  - `mock_redis.save_refresh_token.side_effect = Exception("Redis connection lost")`
- **Выход:** None
- **Поведение:** Обработать ошибку Redis, вернуть None

---

### Класс: `TestUserAuthEdgeCases`
Граничные случаи.

#### test_chek_auth_with_exception_during_jwt
- **Вход:** 
  - `mock_db.check_user()` возвращает 0 (успех)
  - `mock_db.get_public_key_by_email.side_effect = Exception("DB error")`
- **Выход:** response['token'] = -1
- **Поведение:** При ошибке вернуть GENERAL_ERROR

#### test_chek_auth_empty_password
- **Вход:** 
  - `chek_auth("")` с пустым паролем
  - `mock_db.check_user()` возвращает 2
- **Выход:** INVALID_CREDENTIALS_STATUS, token=-1
- **Поведение:** Обработка пустого пароля

---

## Блок Б: Криптография GOST (SignatureUNEP)

### Класс: `TestSignatureUNEP`
Основные операции.

#### test_hash_document
- **Вход:** "Тестовый документ для СЭД"
- **Выход:** bytes, len=32 (256 бит = 32 байта)
- **Поведение:** Хешировать через ГОСТ 34.11-2012 (Стрибог-256)

#### test_generate_keys_success
- **Вход:** 
  - `mock_db.get_public_key_by_email()` возвращает None
  - Вызов `generate_user_keys()`
- **Выход:** (pub_key_b64, priv_key_b64)
  - pub = base64(64 bytes)
  - priv = base64(32 bytes)
- **Поведение:** Генерировать пару ГОСТ ключей

#### test_generate_keys_already_exists
- **Вход:** 
  - Публичный ключ уже в БД: `get_public_key_by_email()` != None
- **Выход:** None
- **Поведение:** Не переписывать существующие ключи

---

#### test_end_to_end_cms_workflow
**СЛОЖНЫЙ ИНТЕГРАЦИОННЫЙ ТЕСТ - "черный ящик":**

- **Вход:**
  1. Генерация ключей GOST
  2. Документ: "Договор №123 от 01.01.2026. Сумма: 100 000 руб."
  
- **Этап 1 - Подписание:**
  - Вызов `signed_hash(test_doc, priv_key_b64)`
  - Выход: `{'signature': bytes, 'signed_attrs_der': bytes, 'content_hash': bytes}`

- **Этап 2 - CMS контейнер:**
  - Вызов `create_cms_container(signed_attrs_der, signature, pub_key_b64)`
  - Выход: bytes (DER-encoded CMS структура, >100 байт)

- **Этап 3 - Верификация (успешная):**
  - Вызов `verify_cms_container(cms_der, original_doc, pub_key_b64)`
  - Выход: `{
      'is_valid': True,
      'checks': {
        'content_hash_match': True,
        'signature_valid': True
      },
      'attrs': [...]
    }`
  - Атрибуты содержат 'content_type' и 'message_digest'

- **Этап 4 - Защита от подделки:**
  - Изменить документ: "Сумма: 900 000 руб."
  - Вызов `verify_cms_container(cms_der, fake_doc, pub_key_b64)`
  - Выход: `{
      'is_valid': False,
      'checks': {
        'content_hash_match': False
      }
    }`

- **Поведение:** Полный цикл криптографической подписи с защитой целостности

---

### Класс: `TestSignatureUNEPHashAndKeys`
Хеширование и ключи.

#### test_hash_document_bytes
- **Вход:** b"Binary document content"
- **Выход:** bytes, len=32
- **Поведение:** Работать с бинарными данными

#### test_hash_document_consistency
- **Вход:** Один документ хеширован дважды
- **Выход:** hash1 == hash2
- **Поведение:** Детерминированный хеш

#### test_hash_document_different_inputs
- **Вход:** "Document 1" vs "Document 2"
- **Выход:** hash1 != hash2
- **Поведение:** Разные входы → разные хеши

#### test_hash_document_empty_string
- **Вход:** ""
- **Выход:** bytes, len=32
- **Поведение:** Даже пустая строка дает валидный хеш

#### test_hash_document_unicode
- **Вход:** "Тестовый документ с кириллицей 日本語 العربية"
- **Выход:** bytes, len=32
- **Поведение:** UTF-8 Unicode поддерживается

---

### Класс: `TestSignatureUNEPVerification`
Проверка подписей.

#### test_signed_hash_valid_keys
- **Вход:** 
  - Валидная пара (pub, priv) ключей
  - "Test document for signing"
- **Выход:** 
  - `{'signature': bytes, 'signed_attrs_der': bytes, 'content_hash': bytes}`
- **Поведение:** Успешно подписать документ

#### test_signed_hash_invalid_private_key
- **Вход:** 
  - `priv_key = base64(b"invalid_key_123")`
- **Выход:** ValueError исключение
- **Поведение:** Валидировать формат ключа

#### test_verify_signature_basic
- **Вход:** 
  - Хеш документа (bytes)
  - Подпись (bytes)
  - Публичный ключ
- **Выход:** bool (True/False)
- **Поведение:** Базовая верификация подписи

---

### Класс: `TestSignatureUNEPCMSEdgeCases`
Граничные случаи CMS.

#### test_verify_cms_with_corrupted_container
- **Вход:** 
  - CMS = b"not_a_valid_cms_der_stream"
- **Выход:** 
  - `{'is_valid': False, 'checks': {'signature_valid': False}}`
- **Поведение:** Обработть поврежденный CMS

#### test_verify_cms_with_wrong_document
- **Вход:** 
  - CMS подписан для "Original document"
  - Проверка с "Modified document"
- **Выход:** 
  - `{'is_valid': False, 'checks': {'content_hash_match': False}}`
- **Поведение:** Хеш не совпадает → подпись невалидна

#### test_verify_cms_without_public_key_fallback
- **Вход:** 
  - `public_key_b64=None`
  - `allow_db_fallback=False`
  - CMS данные
- **Выход:** `{'is_valid': False}`
- **Поведение:** Нельзя верифицировать без публичного ключа

---

## Блок В: PDF Signer

### Класс: `TestPDFSignerValidation`
Валидация параметров подписи.

#### test_validate_signature_params_valid
- **Вход:** page=0, x=100, y=200, width=150, height=80
- **Выход:** (True, "OK")
- **Поведение:** Все параметры в порядке

#### test_validate_signature_params_negative_page
- **Вход:** page=-1
- **Выход:** (False, msg)
- **Поведение:** page >= 0

#### test_validate_signature_params_zero_width
- **Вход:** width=0
- **Выход:** (False, msg)
- **Поведение:** width > 0

#### test_validate_signature_params_zero_height
- **Вход:** height=0
- **Выход:** (False, msg)
- **Поведение:** height > 0

#### test_validate_signature_params_negative_coords
- **Вход:** x=-50
- **Выход:** (False, msg)
- **Поведение:** x, y координаты >= 0

#### test_validate_signature_params_negative_y
- **Вход:** y=-50
- **Выход:** (False, msg)
- **Поведение:** y координаты >= 0

#### test_validate_signature_params_large_values
- **Вход:** page=10, x=1000000, y=2000000, width=5000, height=3000
- **Выход:** (True, "OK")
- **Поведение:** Большие значения допустимы (для масштабирования)

---

### Класс: `TestPDFSignerBase64Handling`
Обработка base64 и PDF.

#### test_add_signature_invalid_pdf_base64
- **Вход:** 
  - PDF base64: "not_a_valid_pdf_base64"
  - Signature: base64(b"fake_signature")
- **Выход:** (result, False)
- **Поведение:** Fail при невалидном PDF

#### test_add_signature_data_uri_handling
- **Вход:** 
  - PDF с префиксом "data:application/pdf;base64,"
  - PNG подпись (1x1 пиксель)
  - Координаты: x=10, y=10, width=50, height=30
- **Выход:** Если успешно, result.startswith("data:application/pdf;base64,")
- **Поведение:** 
  - Удалить data URI префикс
  - Добавить подпись
  - Вернуть результат в том же формате

---

## Блок Г: Интеграционные тесты

### Класс: `TestIntegrationUserWithSignature`
Взаимодействие User и SignatureUNEP.

#### test_user_can_sign_document
- **Вход:** 
  1. User generates keys через SignatureUNEP
  2. Document = "I, the undersigned, approve this"
  3. Подписать через `signed_hash(document, priv_key)`
- **Выход:** 
  - Подпись создана
  - CMS контейнер создан
  - Верификация = True
- **Поведение:** Полный цикл User подписывает документ

---

### Класс: `TestDatabaseFailureScenarios`
Отказы БД.

#### test_user_get_info_db_failure
- **Вход:** 
  - `mock_db.get_user_by_email.side_effect = Exception("Database connection lost")`
- **Выход:** Exception выброшена
- **Поведение:** Не скрывать ошибки БД

#### test_signature_generation_db_failure
- **Вход:** 
  - Генерируем ключи
  - `mock_db.insert_keys_by_email.side_effect = Exception("Database write failed")`
- **Выход:** Ключи сгенерированы (keys != None)
- **Поведение:** 
  - Ключи создаются в памяти
  - Ошибка при сохранении не блокирует возврат

---

# conftest.py

Файл с глобальной конфигурацией и фиксстурами (fixtures).

## Глобальное мокирование модулей

**Проблема:** Модули `config_db`, `database` имеют зависимости на внешние БД.

**Решение:** До импорта `service` создать MagicMock версии:

```python
sys.modules['config_db'] = mock_config
sys.modules['database'] = mock_database_module
```

## Основные фиксстуры

### mock_db
- **Возвращает:** MagicMock имитирующий класс Database
- **Методы:** 
  - `get_user_by_email()` → dict
  - `insert_user()` → True
  - `check_user()` → int (статус код)
  - `get_document_by_id()` → dict
  - `get_all_list_docs()` → list
  - `insert_doc()` → True
  - `get_public_key_by_email()` → str или None
  - `insert_keys_by_email()` → True

### mock_redis
- **Возвращает:** MagicMock имитирующий Redis
- **Методы:**
  - `save_refresh_token()` → True
  - `get_refresh_token()` → "token"
  - `delete_refresh_token()` → True

### user_instance
- **Возвращает:** User объект с test email = "test@domain.com"
- **Использует:** mock_db, mock_redis

### valid_jwt_token
- **Возвращает:** JWT строка (не истекла)
- **Содержит:** sub="123", name="test@domain.com", exp в будущем
- **Подписана:** SECRET_KEY из mock_config

### expired_jwt_token
- **Возвращает:** JWT строка (истекла)
- **exp** = текущее время - 60 сек

### invalid_jwt_token
- **Возвращает:** "invalid.token.not.valid"

### test_user_data
- **Возвращает:** Словарь с тестовыми данными пользователя

### test_document_data
- **Возвращает:** Словарь с тестовыми данными документа

### db_with_mocked_postgres
- **Возвращает:** MagicMock Database с методами для всех операций

### redis_with_mocked_connection
- **Возвращает:** MagicMock DatabaseRedis с методами

---

## Резюме структуры тестов

| Файл | Тестов | Фокус |
|------|--------|-------|
| **test_api_endpoints.py** | ~40 | REST API endpoints, аутентификация, документы, подписи |
| **test_database.py** | ~30 | CRUD операции PostgreSQL и Redis |
| **test_service.py** | ~40 | Бизнес-логика, криптография GOST, User, SignatureUNEP |
| **conftest.py** | - | Фиксстуры и моки |

**Итого:** ~110+ тестов

---

## Паттерны тестирования

### 1. **Параметризация (parametrize)**
```python
@pytest.mark.parametrize("input1, input2, expected", [
    ("data1", "data2", "result1"),
    ("data3", "data4", "result2"),
])
```
Используется для тестирования нескольких сценариев одной функции.

### 2. **Mock и Patch**
```python
@patch('module.function')
mock_db.method.return_value = expected_value
mock_db.method.side_effect = Exception("Error")
```
Замена реальных зависимостей на контролируемые объекты.

### 3. **Fixtures**
Переиспользуемые объекты для тестов (user_instance, mock_db, valid_jwt_token).

### 4. **Интеграционные тесты**
Цепочки операций, проверяющие взаимодействие компонентов.

### 5. **Edge cases**
Граничные значения, ошибки, пустые данные.

---

## Статусы и коды ошибок

| Код | Статус | Значение |
|-----|--------|----------|
| 0 | SUCCESS_STATUS | Успешная операция |
| 2 | INVALID_CREDENTIALS_STATUS | Неверные учетные данные |
| 3 | DB_CONNECTION_ERROR_STATUS | Ошибка подключения БД |
| 99+ | GENERAL_ERROR_STATUS | Неизвестная ошибка |

---

## Ключевые требования и ограничения

1. **JWT токены:**
   - Подписаны SECRET_KEY
   - Содержат `sub` (user ID) и `name` (email)
   - Имеют `exp` (время истечения)

2. **Пароли:**
   - Должны быть захеширован в БД
   - Проверяются через `check_user(email, password)`

3. **Документы:**
   - Hash = SHA256(base64content)
   - Сохраняются с timestamp (Unix time)

4. **Криптография ГОСТ:**
   - Приватный ключ = 32 байта
   - Публичный ключ = 64 байта
   - Хеш Стрибог-256 = 32 байта

5. **Параметры подписи PDF:**
   - page >= 0
   - x, y >= 0
   - width, height > 0

6. **URLs:**
   - Должны быть HTTP или HTTPS
   - Другие протоколы (FTP, etc.) отклоняются
