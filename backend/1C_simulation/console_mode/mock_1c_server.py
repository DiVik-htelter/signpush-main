"""
mock_1c_server.py
=================
Имитирует сторонний сервис (1С Предприятие).

Запускается отдельно:
    python mock_1c_server.py

Порт по умолчанию: 9000
Слушает POST /callback — сюда SignPush API отправит webhook с подписанным документом.
"""

import json
import base64
import hashlib
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Mock 1С Receiver", docs_url="/docs")

received_webhooks: list = []   # Хранит все принятые вебхуки в памяти


@app.post("/callback")
async def receive_signed_document(request: Request):
    """
    SignPush API вызывает этот endpoint после того, как пользователь подписал документ.
    Формат входящего тела (ResponseDoc):
    {
        "document": {
            "id": 42,
            "title": "Договор.pdf (Подписан)",
            "hash": "<sha256>",
            "base64": "<base64 подписанного PDF>",
            "created_at": 1700000000,
            "email": "user@example.com"
        },
        "signatureIMG": { ... } | null,
        "signatureUNEP": "<base64 CMS>" | null,
        "public_key": "<base64 ключ>" | null
    }
    """
    body = await request.json()
    received_at = datetime.now().strftime("%H:%M:%S")

    # --- Красивый вывод в консоль ---
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  ✅  WEBHOOK ПОЛУЧЕН  [{received_at}]")
    print(sep)

    doc = body.get("document", {})
    print(f"  📄 Документ ID  : {doc.get('id')}")
    print(f"  📋 Название     : {doc.get('title')}")
    print(f"  📧 Email        : {doc.get('email')}")
    print(f"  🔒 Hash         : {doc.get('hash', '')[:16]}...")

    sig_unep = body.get("signatureUNEP")
    sig_img  = body.get("signatureIMG")
    pub_key  = body.get("public_key")

    if sig_unep:
        print(f"  ✍️  УНЭП подпись  : {sig_unep[:20]}... (base64)")
    if sig_img:
        print(f"  🖊️  Граф. подпись  : присутствует")
    if pub_key:
        print(f"  🔑 Публичный ключ: {pub_key[:20]}... (base64)")

    # Проверка целостности: hash от base64 должен совпадать
    b64_payload = doc.get("base64", "")
    clean = b64_payload.split("base64,")[-1] if "base64," in b64_payload else b64_payload
    computed_hash = hashlib.sha256(clean.encode()).hexdigest()
    hash_ok = computed_hash == doc.get("hash", "")
    print(f"  🔎 Хеш совпадает : {'✅ ДА' if hash_ok else '❌ НЕТ'}")
    print(sep + "\n")

    received_webhooks.append({
        "received_at": received_at,
        "document_id": doc.get("id"),
        "title": doc.get("title"),
        "email": doc.get("email"),
        "hash_ok": hash_ok,
        "has_unep": bool(sig_unep),
        "has_img": bool(sig_img),
    })

    return JSONResponse(content={"status": "ok", "message": "Webhook received"})


@app.get("/received")
async def get_received():
    """Возвращает список всех полученных вебхуков (для отладки)."""
    return {"count": len(received_webhooks), "webhooks": received_webhooks}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mock-1c-receiver"}


if __name__ == "__main__":
    print("=" * 60)
    print("  🏁  Mock 1С Receiver запущен")
    print("  Слушаю вебхуки на  POST http://localhost:9000/callback")
    print("  Swagger-UI:             http://localhost:9000/docs")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="warning")
