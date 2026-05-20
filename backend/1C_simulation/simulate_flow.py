"""
simulate_flow.py
================
Пошаговая демонстрация полного сценария:
  1С → SignPush API → пользователь подписывает → SignPush API → webhook → 1С

Запуск:
    python simulate_flow.py

Перед запуском убедитесь, что:
  • SignPush API запущен на SIGN_PUSH_URL (по умолчанию http://localhost:8000)
  • mock_1c_server.py запущен на порту 9000 (или задайте CALLBACK_URL вручную)
  • В БД есть пользователь с SIGNER_EMAIL (или зарегистрируйте его — шаг 0)
"""

import sys
import time
import base64
import hashlib
import json
import requests

# ──────────────────────────────────────────────
# НАСТРОЙКИ — меняйте под своё окружение
# ──────────────────────────────────────────────
SIGN_PUSH_URL = "http://localhost:8000"   # Адрес вашего FastAPI-приложения
CALLBACK_URL  = "http://localhost:9000/callback"  # Адрес mock_1c_server.py

SIGNER_EMAIL    = "admin@gmail.com"   # Email пользователя, которому отправляем документ
SIGNER_PASSWORD = "adminadmin"       # Пароль (нужен только для шага 0)

# Тип подписи: "unep" или "img"
SIGNATURE_TYPE = "img"  # Меняйте здесь для тестирования графической подписи
# ──────────────────────────────────────────────


def sep(title=""):
    line = "─" * 56
    if title:
        pad = (56 - len(title) - 2) // 2
        print(f"\n╔{'═' * 56}╗")
        print(f"║{' ' * pad} {title} {' ' * (56 - pad - len(title) - 1)}║")
        print(f"╚{'═' * 56}╝")
    else:
        print(f"\n{line}")


def ok(msg):  print(f"  ✅  {msg}")
def err(msg): print(f"  ❌  {msg}"); sys.exit(1)
def info(msg):print(f"  ℹ️   {msg}")
def show_response(r):
    try:
        data = r.json()
        print(f"  HTTP {r.status_code} → {json.dumps(data, ensure_ascii=False, indent=4)}")
    except Exception:
        print(f"  HTTP {r.status_code} → {r.text[:300]}")


# ══════════════════════════════════════════════
# ШАГ 0: (Опционально) Регистрация пользователя
# ══════════════════════════════════════════════
def step0_register_user():
    sep("ШАГ 0 — Регистрация тестового пользователя")
    info(f"POST {SIGN_PUSH_URL}/api/v1/user/register")

    payload = {
        "email":      SIGNER_EMAIL,
        "password":   SIGNER_PASSWORD,
        "first_name": "Иван",
        "last_name":  "Тестов"
    }
    r = requests.post(f"{SIGN_PUSH_URL}/api/v1/user/register", json=payload)
    show_response(r)

    if r.status_code == 400 and "already exists" in r.text:
        ok("Пользователь уже существует — продолжаем")
    elif r.ok:
        ok("Пользователь зарегистрирован")
    else:
        err("Не удалось зарегистрировать пользователя")


# ══════════════════════════════════════════════════════════════
# ШАГ 1: Создаём минимальный PDF в base64 для теста
# ══════════════════════════════════════════════════════════════
def make_minimal_pdf_base64() -> str:
    """Возвращает base64 крошечного, но валидного PDF-файла."""
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>\nstream\nBT /F1 24 Tf 100 700 Td (Test Doc) Tj ET\nendstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f\n"
        b"0000000009 00000 n\n0000000058 00000 n\n"
        b"0000000115 00000 n\n0000000274 00000 n\n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n370\n%%EOF"
    )
    return base64.b64encode(pdf_bytes).decode()


# ══════════════════════════════════════════════════════════════
# ШАГ 1: 1С отправляет документ на подпись
# ══════════════════════════════════════════════════════════════
def step1_send_document_from_1c() -> int:
    sep(f"ШАГ 1 — 1С отправляет документ на подпись [{SIGNATURE_TYPE.upper()}]")
    info(f"POST {SIGN_PUSH_URL}/api/v1/document/sign/{SIGNATURE_TYPE}")

    pdf_b64 = make_minimal_pdf_base64()
    doc_hash = hashlib.sha256(pdf_b64.encode()).hexdigest()
    created_at = int(time.time())

    payload = {
        "endpoint":   CALLBACK_URL,
        "deadlite_at": created_at + 86400,  # Срок: сутки
        "document": {
            "id":         0,              # ID нашей БД — заглушка, сервер сам присвоит
            "title":      "Договор_тест.pdf",
            "hash":       doc_hash,
            "base64":     pdf_b64,
            "created_at": created_at,
            "email":      SIGNER_EMAIL    # Кому адресован документ
        }
    }

    info(f"callback URL       : {CALLBACK_URL}")
    info(f"адресат (подписант): {SIGNER_EMAIL}")
    info(f"SHA-256 документа  : {doc_hash[:16]}...")

    r = requests.post(
        f"{SIGN_PUSH_URL}/api/v1/document/sign/{SIGNATURE_TYPE}",
        json=payload,
        timeout=15
    )
    show_response(r)

    if not r.ok:
        err("Сервер вернул ошибку на шаге 1")

    data = r.json()
    doc_id = data.get("document_id")
    if not doc_id:
        err("Не получили document_id в ответе")

    ok(f"Документ зарегистрирован. document_id = {doc_id}")
    return doc_id


# ══════════════════════════════════════════════════════════════
# ШАГ 2: Имитируем подписание пользователем
# (в реальности это делает фронтенд/мобильное приложение)
# ══════════════════════════════════════════════════════════════
def step2_simulate_signing(document_id: int):
    sep("ШАГ 2 — Имитация подписания пользователем")

    if SIGNATURE_TYPE == "unep":
        info("Тип: УНЭП — генерируем фейковый CMS-контейнер (base64)")
        # В реальном сценарии здесь будет настоящая криптографическая подпись
        fake_cms = base64.b64encode(b"FAKE_CMS_SIGNATURE_CONTAINER").decode()
        fake_key = base64.b64encode(b"FAKE_PUBLIC_KEY").decode()
        sign_payload = {
            "document_id":   document_id,
            "callback_url":  None,       # Берётся из реестра (зарегистрировали в шаге 1)
            "signatureUNEP": fake_cms,
            "public_key":    fake_key,
            "signatureIMG":  None,
        }
    else:
        info("Тип: IMG — генерируем фейковое PNG изображение подписи (1×1 px)")
        # 1×1 прозрачный PNG
        tiny_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        fake_img_b64 = base64.b64encode(tiny_png).decode()
        sign_payload = {
            "document_id":  document_id,
            "callback_url": None,
            "signatureIMG": {
                "data": fake_img_b64,
                "page": 0,
                "x": 100, "y": 700, "w": 150, "h": 50,
            },
            "signatureUNEP": None,
            "public_key":   None,
        }

    info(f"POST {SIGN_PUSH_URL}/api/v1/document/webhook")
    r = requests.post(
        f"{SIGN_PUSH_URL}/api/v1/document/webhook",
        json=sign_payload,
        timeout=15
    )
    show_response(r)

    if not r.ok:
        err("Сервер вернул ошибку на шаге 2")

    ok("Запрос на отправку вебхука принят сервером (background task запущен)")


# ══════════════════════════════════════════════════════════════
# ШАГ 3: Ждём вебхук на mock_1c_server и проверяем его получение
# ══════════════════════════════════════════════════════════════
def step3_verify_webhook_received(max_wait: int = 10):
    sep("ШАГ 3 — Проверяем, что mock_1c_server получил webhook")
    info(f"Ждём до {max_wait} секунд...")

    for attempt in range(max_wait):
        time.sleep(1)
        try:
            r = requests.get("http://localhost:9000/received", timeout=5)
            data = r.json()
            if data.get("count", 0) > 0:
                last = data["webhooks"][-1]
                ok(f"Webhook получен на попытке {attempt + 1}!")
                print()
                print(f"  📄 Документ ID      : {last.get('document_id')}")
                print(f"  📋 Название         : {last.get('title')}")
                print(f"  📧 Email            : {last.get('email')}")
                print(f"  🔒 Хеш совпадает   : {'✅' if last.get('hash_ok') else '❌'}")
                print(f"  ✍️  Есть УНЭП подпись: {'✅' if last.get('has_unep') else '—'}")
                print(f"  🖊️  Есть IMG подпись : {'✅' if last.get('has_img') else '—'}")
                return
            else:
                print(f"  ⏳ Ожидание... ({attempt + 1}/{max_wait})")
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  mock_1c_server недоступен. Убедитесь, что он запущен: python mock_1c_server.py")
            return

    print("\n  ⚠️  Webhook не получен за отведённое время.")
    print("  Возможные причины:")
    print("    • SignPush API не смог достучаться до CALLBACK_URL")
    print("    • mock_1c_server.py не запущен (порт 9000)")
    print("    • Проверьте лог SignPush API на ошибки отправки")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print()
    print("╔════════════════════════════════════════════════════════╗")
    print("║     SignPush — симуляция полного цикла подписания      ║")
    print("║   1С → API → подпись → webhook → 1С                   ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()
    print(f"  SignPush API : {SIGN_PUSH_URL}")
    print(f"  Callback URL : {CALLBACK_URL}")
    print(f"  Подписант    : {SIGNER_EMAIL}")
    print(f"  Тип подписи  : {SIGNATURE_TYPE.upper()}")

    # Шаг 0: регистрация (раскомментируйте если пользователя ещё нет)
    # step0_register_user()

    # Шаг 1: 1С отправляет документ
    doc_id = step1_send_document_from_1c()

    # Небольшая пауза — даём серверу сохранить всё в БД
    time.sleep(0.5)

    # Шаг 2: пользователь «подписывает» документ
    step2_simulate_signing(doc_id)

    # Небольшая пауза — BackgroundTask запускается после ответа
    time.sleep(1)

    # Шаг 3: проверяем, что mock_1c_server получил вебхук
    step3_verify_webhook_received(max_wait=10)

    sep()
    print("  🏁  Симуляция завершена")
    print()
    print("  Дополнительно можно проверить:")
    print(f"    Swagger SignPush : {SIGN_PUSH_URL}/api/swagger")
    print(f"    Swagger 1С mock  : http://localhost:9000/docs")
    print(f"    Все вебхуки      : http://localhost:9000/received")
    print()
