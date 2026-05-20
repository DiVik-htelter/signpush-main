"""
simulate_1c.py
==============
Интерактивный симулятор 1С Предприятия для тестирования SignPush API.

Запуск:
    python simulate_1c.py

Настройки сценариев — в файле config.py
"""

import sys
import time
import base64
import hashlib
import json
import os
from datetime import datetime

import config

import os
# Удаляем переменные полностью, а не просто зануляем
for var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    if var in os.environ:
        del os.environ[var]
        
try:
    import requests
except ImportError:
    print("Установите зависимость: pip install requests")
    sys.exit(1)



# ══════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ УТИЛИТЫ
# ══════════════════════════════════════════════════════════════

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
GREY   = "\033[90m"
WHITE  = "\033[97m"


def c(color, text):
    return f"{color}{text}{RESET}"


def header(title: str):
    width = 60
    inner = f"  {title}  "
    pad = (width - len(inner)) // 2
    print()
    print(c(CYAN, "╔" + "═" * width + "╗"))
    print(c(CYAN, "║") + " " * pad + c(BOLD + WHITE, inner) + " " * (width - pad - len(inner)) + c(CYAN, "║"))
    print(c(CYAN, "╚" + "═" * width + "╝"))


def divider(label=""):
    if label:
        line = f"  {label}  "
        pad = "─" * 3
        print(c(GREY, f"\n  {pad} {label} {pad}"))
    else:
        print(c(GREY, "\n  " + "─" * 54))


def ok(msg):
    print(f"  {c(GREEN, '✅')} {msg}")


def fail(msg):
    print(f"  {c(RED, '❌')} {msg}")


def info(msg):
    print(f"  {c(BLUE, 'ℹ')}  {msg}")


def warn(msg):
    print(f"  {c(YELLOW, '⚠')}  {msg}")


def label(key, val):
    print(f"  {c(GREY, key + ':'): <30} {c(WHITE, str(val))}")


def print_response(r: "requests.Response"):
    """Красиво выводит HTTP-ответ от API."""
    divider("Ответ от API")
    status_color = GREEN if r.ok else RED
    print(f"  {c(BOLD, 'HTTP')} {c(status_color, str(r.status_code))}", end="  ")

    try:
        data = r.json()
        print()
        lines = json.dumps(data, ensure_ascii=False, indent=4).split("\n")
        for line in lines:
            # Подсвечиваем ключи
            if '":' in line:
                key_part, _, val_part = line.partition('":')
                print(f"  {c(CYAN, key_part + chr(34))}: {val_part}")
            else:
                print(f"  {line}")
    except Exception:
        print(r.text[:500])

    print()
    return r.ok


def make_minimal_pdf_base64() -> str:
    """Создаёт минимальный валидный PDF и возвращает его в base64."""
    ts = str(int(time.time()))
    content_stream = f"BT /F1 12 Tf 72 720 Td (SignPush Test Document {ts}) Tj ET"
    stream_len = len(content_stream)
    pdf = (
        f"%PDF-1.4\n"
        f"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        f"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        f"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        f"/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>  >>endobj\n"
        f"4 0 obj<</Length {stream_len}>>\nstream\n{content_stream}\nendstream endobj\n"
        f"xref\n0 5\n0000000000 65535 f \n"
        f"trailer<</Size 5/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )
    return base64.b64encode(pdf.encode()).decode()


def load_pdf_as_base64(path: str) -> str:
    """Читает PDF с диска и возвращает base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def resolve_callback(override) -> str:
    return override if override else config.CALLBACK_URL


def post(endpoint: str, payload: dict) -> "requests.Response":
    url = config.SIGN_PUSH_URL.rstrip("/") + endpoint
    info(f"POST {url}")
    return requests.post(url, json=payload, timeout=config.REQUEST_TIMEOUT)


def get(url: str) -> "requests.Response":
    return requests.get(url, timeout=config.REQUEST_TIMEOUT)


# ══════════════════════════════════════════════════════════════
#  СЦЕНАРИЙ 1 — Регистрация пользователя
# ══════════════════════════════════════════════════════════════

def scenario_register():
    header("СЦЕНАРИЙ 1 — Регистрация пользователя")
    cfg = config.SCENARIO_REGISTER

    label("Email",     cfg["email"])
    label("Имя",       cfg["first_name"])
    label("Фамилия",   cfg["last_name"])
    label("Пароль",    "*" * len(cfg["password"]))

    payload = {
        "email":      cfg["email"],
        "password":   cfg["password"],
        "first_name": cfg["first_name"],
        "last_name":  cfg["last_name"],
    }

    try:
        r = post("/api/v1/user/register", payload)
        success = print_response(r)

        if r.status_code == 400 and "already exists" in r.text:
            warn("Пользователь с таким email уже зарегистрирован")
        elif success:
            ok("Пользователь успешно зарегистрирован")
        else:
            fail("Ошибка регистрации — смотрите ответ выше")

    except requests.exceptions.ConnectionError:
        fail(f"Нет соединения с {config.SIGN_PUSH_URL}")
    except Exception as e:
        fail(f"Исключение: {e}")


# ══════════════════════════════════════════════════════════════
#  СЦЕНАРИЙ 2 — Отправка документа на подпись IMG
# ══════════════════════════════════════════════════════════════

def scenario_send_img():
    header("СЦЕНАРИЙ 2 — Отправка документа на подпись (IMG)")
    cfg = config.SCENARIO_SEND_IMG
    callback = resolve_callback(cfg.get("callback_url"))
    now = int(time.time())
    deadline = now + cfg["deadline_offset_sec"]

    label("Подписант",      cfg["signer_email"])
    label("Документ",       cfg["document_title"])
    label("Callback URL",   callback)
    label("Срок подписания", datetime.fromtimestamp(deadline).strftime("%d.%m.%Y %H:%M"))

    divider("Генерация тестового PDF")
    pdf_b64 = make_minimal_pdf_base64()
    doc_hash = hashlib.sha256(pdf_b64.encode()).hexdigest()
    info(f"SHA-256: {doc_hash[:24]}...")
    ok("Тестовый PDF сгенерирован")

    payload = {
        "endpoint":    callback,
        "deadlite_at": deadline,
        "document": {
            "id":         0,
            "title":      cfg["document_title"],
            "hash":       doc_hash,
            "base64":     pdf_b64,
            "created_at": now,
            "email":      cfg["signer_email"],
        },
    }

    try:
        r = post("/api/v1/document/sign/img", payload)
        success = print_response(r)

        if success:
            doc_id = r.json().get("document_id")
            ok(f"Документ зарегистрирован. document_id = {c(YELLOW, str(doc_id))}")
            _wait_for_webhook(doc_id)
        else:
            fail("Сервер вернул ошибку — смотрите ответ выше")

    except requests.exceptions.ConnectionError:
        fail(f"Нет соединения с {config.SIGN_PUSH_URL}")
    except Exception as e:
        fail(f"Исключение: {e}")


# ══════════════════════════════════════════════════════════════
#  СЦЕНАРИЙ 3 — Отправка документа на подпись УНЭП
# ══════════════════════════════════════════════════════════════

def scenario_send_unep():
    header("СЦЕНАРИЙ 3 — Отправка документа на подпись (УНЭП)")
    cfg = config.SCENARIO_SEND_UNEP
    callback = resolve_callback(cfg.get("callback_url"))
    now = int(time.time())
    deadline = now + cfg["deadline_offset_sec"]

    label("Подписант",       cfg["signer_email"])
    label("Документ",        cfg["document_title"])
    label("Callback URL",    callback)
    label("Срок подписания", datetime.fromtimestamp(deadline).strftime("%d.%m.%Y %H:%M"))

    divider("Генерация тестового PDF")
    pdf_b64 = make_minimal_pdf_base64()
    doc_hash = hashlib.sha256(pdf_b64.encode()).hexdigest()
    info(f"SHA-256: {doc_hash[:24]}...")
    ok("Тестовый PDF сгенерирован")

    payload = {
        "endpoint":    callback,
        "deadlite_at": deadline,
        "document": {
            "id":         0,
            "title":      cfg["document_title"],
            "hash":       doc_hash,
            "base64":     pdf_b64,
            "created_at": now,
            "email":      cfg["signer_email"],
        },
    }

    try:
        r = post("/api/v1/document/sign/unep", payload)
        success = print_response(r)

        if success:
            doc_id = r.json().get("document_id")
            ok(f"Документ зарегистрирован. document_id = {c(YELLOW, str(doc_id))}")
            _wait_for_webhook(doc_id)
        else:
            fail("Сервер вернул ошибку — смотрите ответ выше")

    except requests.exceptions.ConnectionError:
        fail(f"Нет соединения с {config.SIGN_PUSH_URL}")
    except Exception as e:
        fail(f"Исключение: {e}")


# ══════════════════════════════════════════════════════════════
#  СЦЕНАРИЙ 4 — Верификация УНЭП подписи
# ══════════════════════════════════════════════════════════════

def scenario_verify_unep():
    header("СЦЕНАРИЙ 4 — Верификация УНЭП подписи")
    cfg = config.SCENARIO_VERIFY_UNEP

    label("Email подписанта", cfg["signer_email"])

    # ── Формируем тело запроса ───────────────────────────────
    payload: dict = {
        "email":    cfg["signer_email"],
        "base64":   cfg["signature_base64"],
    }

    if cfg.get("document_id") is not None:
        payload["document_id"] = cfg["document_id"]
        label("Режим", "по document_id из БД")
        label("document_id", cfg["document_id"])

    elif cfg.get("pdf_path"):
        path = cfg["pdf_path"]
        if not os.path.isfile(path):
            fail(f"Файл не найден: {path}")
            warn("Укажите корректный pdf_path в config.py → SCENARIO_VERIFY_UNEP")
            return

        divider("Чтение PDF с диска")
        info(f"Файл: {path}")
        pdf_b64 = load_pdf_as_base64(path)
        doc_hash = hashlib.sha256(pdf_b64.encode()).hexdigest()
        size_kb = os.path.getsize(path) // 1024
        ok(f"Прочитан ({size_kb} КБ), SHA-256: {doc_hash[:24]}...")

        payload["document"] = {
            "id":         0,
            "title":      os.path.basename(path),
            "hash":       doc_hash,
            "base64":     pdf_b64,
            "created_at": int(time.time()),
            "email":      cfg["signer_email"],
        }
        label("Режим", "по PDF-файлу с диска")

    else:
        fail("Укажите document_id или pdf_path в config.py → SCENARIO_VERIFY_UNEP")
        return

    if not cfg.get("signature_base64"):
        warn("signature_base64 пустой в config.py — API, скорее всего, вернёт ошибку.")
        warn("Вставьте реальную УНЭП подпись (base64) из webhook-ответа.")

    if cfg.get("verify_callback_url"):
        payload["endpoint"] = cfg["verify_callback_url"]
        label("Callback верификации", cfg["verify_callback_url"])

    try:
        r = post("/api/v1/document/verify/unep", payload)
        success = print_response(r)

        if success:
            is_valid = r.json().get("is_valid", False)
            if is_valid:
                ok("Подпись валидна ✍️")
            else:
                warn("Подпись НЕ валидна (или тестовая заглушка — проверьте signature_base64 в config.py)")
        else:
            fail("Сервер вернул ошибку")

    except requests.exceptions.ConnectionError:
        fail(f"Нет соединения с {config.SIGN_PUSH_URL}")
    except Exception as e:
        fail(f"Исключение: {e}")


# ══════════════════════════════════════════════════════════════
#  СЦЕНАРИЙ 5 — Просмотр входящих webhook-ов
# ══════════════════════════════════════════════════════════════

def scenario_check_webhooks():
    header("СЦЕНАРИЙ 5 — Просмотр входящих webhook-ов (mock 1С)")
    cfg = config.SCENARIO_CHECK_WEBHOOKS
    url = cfg["mock_server_url"].rstrip("/") + "/received"

    try:
        r = get(url)
        data = r.json()
        count = data.get("count", 0)
        webhooks = data.get("webhooks", [])

        if count == 0:
            warn("Webhook-и ещё не получены")
            info("Убедитесь, что mock_1c_server.py запущен, и выполните сценарий 2 или 3")
            return

        ok(f"Получено webhook-ов: {c(YELLOW, str(count))}")
        divider()

        for i, wh in enumerate(webhooks, 1):
            print(f"  {c(BOLD, f'#{i}')}  [{wh.get('received_at', '?')}]")
            label("    document_id",   wh.get("document_id", "—"))
            label("    Название",      wh.get("title", "—"))
            label("    Email",         wh.get("email", "—"))
            label("    Хеш совпадает", "✅ Да" if wh.get("hash_ok") else "❌ Нет")
            label("    УНЭП подпись",  "✅ есть" if wh.get("has_unep") else "—")
            label("    IMG подпись",   "✅ есть" if wh.get("has_img") else "—")
            if i < count:
                print()

    except requests.exceptions.ConnectionError:
        fail(f"mock_1c_server.py недоступен по адресу {cfg['mock_server_url']}")
        warn("Запустите: python mock_1c_server.py")
    except Exception as e:
        fail(f"Исключение: {e}")


# ══════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНАЯ: Ожидание входящего webhook
# ══════════════════════════════════════════════════════════════

def _wait_for_webhook(doc_id):
    """
    После регистрации документа ждём, пока пользователь его «подпишет»
    через endpoint /api/v1/document/webhook — и mock-сервер получит callback.

    В реальности подпись ставится пользователем через UI.
    Здесь у нас два варианта:
      • Автоматическая имитация (вызываем /api/v1/document/webhook сами)
      • Ручная — ждём пока вы сделаете это из другого места
    """
    divider("Следующий шаг")
    print(f"""
  Документ ожидает подписи пользователем.

  Чтобы имитировать подписание — вызовите вручную:

    {c(CYAN, 'POST ' + config.SIGN_PUSH_URL + '/api/v1/document/webhook')}

  Тело запроса (УНЭП):
  {c(GREY, json.dumps({
      "document_id":   doc_id,
      "callback_url":  None,
      "signatureUNEP": "<base64 CMS подписи>",
      "public_key":    "<base64 публичного ключа>",
      "signatureIMG":  None,
  }, ensure_ascii=False, indent=2))}

  Или используйте Swagger UI:
    {c(CYAN, config.SIGN_PUSH_URL + '/api/swagger')}

  После подписания webhook придёт на:
    {c(CYAN, config.CALLBACK_URL)}

  Запустите сценарий {c(YELLOW, '5')} чтобы увидеть входящие webhook-и.
    """)


# ══════════════════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ══════════════════════════════════════════════════════════════

MENU_ITEMS = {
    "1": ("Регистрация нового пользователя",           scenario_register),
    "2": ("Отправить документ на подпись IMG",          scenario_send_img),
    "3": ("Отправить документ на подпись УНЭП",         scenario_send_unep),
    "4": ("Верифицировать УНЭП подпись документа",      scenario_verify_unep),
    "5": ("Просмотреть входящие webhook-и (mock 1С)",   scenario_check_webhooks),
}


def print_menu():
    width = 60
    print()
    print(c(CYAN, "╔" + "═" * width + "╗"))
    print(c(CYAN, "║") + c(BOLD + WHITE, "  SignPush · Симулятор 1С Предприятия".center(width)) + c(CYAN, "║"))
    print(c(CYAN, "╠" + "═" * width + "╣"))

    for key, (label_text, _) in MENU_ITEMS.items():
        line = f"  [{key}]  {label_text}"
        padding = width - len(line)
        print(c(CYAN, "║") + c(WHITE, line) + " " * padding + c(CYAN, "║"))

    print(c(CYAN, "╠" + "═" * width + "╣"))
    quit_line = "  [0]  Выход"
    print(c(CYAN, "║") + c(GREY, quit_line) + " " * (width - len(quit_line)) + c(CYAN, "║"))
    print(c(CYAN, "╚" + "═" * width + "╝"))

    # Статус окружения
    print()
    print(c(GREY, f"  API          : {config.SIGN_PUSH_URL}"))
    print(c(GREY, f"  Callback URL : {config.CALLBACK_URL}"))
    print(c(GREY, f"  Настройки    : config.py"))
    print()


def main():
    # Проверяем доступность API при старте
    print()
    try:
        r = requests.get(config.SIGN_PUSH_URL + "/api/swagger", timeout=3)
        api_status = c(GREEN, "доступен ✅")
    except Exception:
        api_status = c(RED, "недоступен ❌  (убедитесь, что API запущен)")

    print(f"  SignPush API — {api_status}")

    try:
        r = requests.get(config.SCENARIO_CHECK_WEBHOOKS["mock_server_url"] + "/health", timeout=2)
        mock_status = c(GREEN, "запущен ✅")
    except Exception:
        mock_status = c(YELLOW, "не запущен ⚠️  (python mock_1c_server.py)")

    print(f"  Mock 1С      — {mock_status}")

    while True:
        print_menu()

        try:
            choice = input(c(BOLD, "  Введите номер сценария: ")).strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {c(GREY, 'Выход.')}\n")
            break

        if choice == "0":
            print(f"\n  {c(GREY, 'Выход.')}\n")
            break

        if choice in MENU_ITEMS:
            _, handler = MENU_ITEMS[choice]
            handler()
            input(c(GREY, "\n  Нажмите Enter для возврата в меню..."))
        else:
            warn(f"Неизвестный выбор: «{choice}». Введите число от 0 до {len(MENU_ITEMS)}.")


if __name__ == "__main__":
    main()
