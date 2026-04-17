# API для сторонних сервисов (callback интеграция)

Этот документ описывает внешние роуты, которые не требуют токена пользовательской сессии.
Они предназначены для интеграции с 1С и другими внешними системами.

## Общие правила

- Базовый URL локально: `http://localhost:8000`
- Формат данных: `application/json`
- Аутентификация сессионным токеном **не требуется**
- Для отправки документов обязательно передавайте корректный `hash` (SHA-256 от base64 payload документа)

---

## 1) Регистрация пользователя

### Endpoint
`POST /api/v1/user/register`

### Тело запроса
```json
{
  "email": "user@example.com",
  "password": "StrongPass123",
  "first_name": "Иван",
  "last_name": "Иванов"
}
```

### Успешный ответ
```json
{
  "status": 0,
  "message": "Успешная регистрация!"
}
```

---

## 2) Передать документ на подпись УНЭП

### Endpoint
`POST /api/v1/document/sign/unep`

### Тело запроса
```json
{
  "endpoint": "https://third-party.example.com/callback/signed",
  "deadlite_at": 1799999999,
  "document": {
    "id": 10001,
    "title": "contract_2026.pdf",
    "hash": "<sha256_base64_payload>",
    "base64": "data:application/pdf;base64,JVBERi0xLjQKJ...",
    "created_at": 1790000000,
    "email": "user@example.com"
  }
}
```

### Успешный ответ
```json
{
  "success": true,
  "message": "Документ принят и поставлен в очередь на подпись",
  "document_id": 321,
  "endpoint": "https://third-party.example.com/callback/signed",
  "signature_type": "unep"
}
```

---

## 3) Передать документ на графическую подпись

### Endpoint
`POST /api/v1/document/sign/img`

Тело и формат ответа такие же, как у `/api/v1/document/sign/unep`, но `signature_type` будет `img`.

---

## 4) Вернуть подписанный документ на внешний сервис (webhook запуск)

Этот endpoint запускает фоновую отправку подписанного документа на callback URL.

### Endpoint
`POST /api/v1/document/webhook`

### Тело запроса
```json
{
  "document_id": 321,
  "callback_url": "https://third-party.example.com/callback/signed",
  "signatureIMG": {
    "page_number": 0,
    "x": 120,
    "y": 180,
    "width": 220,
    "height": 90
  },
  "signatureUNEP": "MII...base64...",
  "public_key": "BASE64_PUBLIC_KEY"
}
```

### Примечания
- `callback_url` можно не передавать, если он был сохранен ранее через `/api/v1/document/sign/unep` или `/api/v1/document/sign/img`.
- `signatureIMG`, `signatureUNEP`, `public_key` — опциональны.

### Успешный ответ
```json
{
  "success": true,
  "message": "Signed document will be sent shortly"
}
```

---

## 5) Проверить валидность подписи УНЭП

### Endpoint
`POST /api/v1/document/verify/unep`

Поддерживаются **2 режима**:

1. Проверка по `document_id` (документ уже есть в БД)
2. Проверка по `document` (если документ не хранится в БД)

### Вариант A: проверка по document_id
```json
{
  "base64": "MII...signature_base64...",
  "email": "user@example.com",
  "document_id": 321
}
```

### Вариант B: проверка по документу из запроса
```json
{
  "base64": "MII...signature_base64...",
  "email": "user@example.com",
  "document": {
    "id": 555,
    "title": "external_doc.pdf",
    "hash": "<sha256_base64_payload>",
    "base64": "data:application/pdf;base64,JVBERi0xLjQKJ...",
    "created_at": 1790000000,
    "email": "user@example.com"
  }
}
```

### Дополнительно
Можно передать `endpoint`, чтобы сервис продублировал результат проверки на внешний callback:
```json
{
  "base64": "MII...signature_base64...",
  "email": "user@example.com",
  "document_id": 321,
  "endpoint": "https://third-party.example.com/callback/verify"
}
```

### Успешный ответ
```json
{
  "is_valid": true,
  "message": "Подпись валидна"
}
```

---

## Как правильно посчитать hash

Нужно считать SHA-256 от **payload части base64**, то есть без префикса `data:application/pdf;base64,`.

### Пример на Python
```python
from hashlib import sha256

base64_document = "data:application/pdf;base64,JVBERi0xLjQKJ..."
payload = base64_document.split(",", 1)[1] if "," in base64_document else base64_document
hash_value = sha256(payload.encode()).hexdigest()
print(hash_value)
```

---

## Минимальный cURL пример (передача на УНЭП)

```bash
curl -X POST "http://localhost:8000/api/v1/document/sign/unep" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://third-party.example.com/callback/signed",
    "deadlite_at": 1799999999,
    "document": {
      "id": 10001,
      "title": "contract_2026.pdf",
      "hash": "PUT_SHA256_HERE",
      "base64": "data:application/pdf;base64,JVBERi0xLjQKJ...",
      "created_at": 1790000000,
      "email": "user@example.com"
    }
  }'
```

---

## Типовые ошибки

- `400 Hash документа не совпадает с содержимым base64` — неверно вычислен `hash`
- `404 Пользователь-подписант не найден` — сначала зарегистрируйте пользователя
- `400 Invalid callback URL` — `endpoint`/`callback_url` должен начинаться с `http://` или `https://`
- `404 Документ не найден` — неверный `document_id`
