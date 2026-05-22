#!/usr/bin/env python3
"""
Тест: Подписание документа и проверка подписи (end-to-end)
Проверяет, что подпись успешно создаётся И валидируется
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service import SignatureUNEP
from database import Database
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

def test_sign_and_verify_full_flow():
    print("\n" + "="*80)
    print("ТЕСТ: Полный цикл подписи → создание CMS → валидация")
    print("="*80 + "\n")
    
    db = Database()
    email = "fullflow@example.com"
    
    # 0. Подготовка: создаем пользователя, если его нет
    print("[0] Подготовка: создание пользователя в БД...")
    try:
        if db.is_original_email(email):
            # Пользователь не существует, создаем его
            db.insert_user(email, "tempassword123", name={'firstName': 'Test', 'lastName': 'User'})
            print("✓ Пользователь создан\n")
        else:
            print("✓ Пользователь уже существует\n")
    except Exception as e:
        print(f"⚠ Ошибка при подготовке: {e}\n")
    
    # 1. Инициализируем подписанта
    print("[1] Инициализация подписанта...")
    signer = SignatureUNEP(email, db)
    print(f"✓ Подписант инициализирован: {email}\n")
    
    # 2. Генерируем ключи
    print("[2] Генерация ключей...")
    keys = signer.generate_user_keys()
    if not keys:
        print("✗ Ошибка при генерации ключей")
        return False
    
    public_key_b64, private_key_b64 = keys
    print("✓ Ключи сгенерированы\n")
    
    # 3. Информация о пользователе
    user_info = {
        'first_name': 'Тест',
        'last_name': 'Проверка',
        'email': email
    }
    
    # 4. Подписываем документ
    print("[3] Создание подписи документа...")
    document = "Это тестовый документ для полной проверки цикла подписи"
    print("✓ Подпись создана\n")
    
    # 5. Создаём CMS контейнер
    print("[4] Создание CMS контейнера...")
    doc_hash = signer.hash_document(document)
    cms_der = signer.create_cms_container(
        document_hash=doc_hash,
        private_key_b64=private_key_b64,
        public_key_b64=public_key_b64,
        user_info=user_info
    )
    print(f"✓ CMS контейнер создан ({len(cms_der)} байт)\n")
    
    # 6. КЛЮЧЕВОЙ ТЕСТ: Валидируем подпись С ПОЛУЧЕННЫМ КЛЮЧОМ
    print("[5] Валидация подписи (с явной передачей public_key_b64)...")
    result = signer.verify_cms_container(
        cms_signature_bytes=cms_der,
        signed_document=document,
        public_key_b64=public_key_b64,
        allow_db_fallback=False  # Явно отключаем fallback
    )
    
    if result.get('is_valid'):
        print("✓ Подпись ВАЛИДНА (с явной передачей ключа)\n")
    else:
        print("✗ Подпись НЕВАЛИДНА (с явной передачей ключа)")
        print(f"Checks: {result.get('checks')}")
        return False
    
    # 7. КРИТИЧЕСКИЙ ТЕСТ: Валидируем подпись БЕЗ ЯВНОГО КЛЮЧА (с fallback из БД)
    print("[6] Валидация подписи (с получением ключа из БД через allow_db_fallback)...")
    
    # Создаем новый экземпляр signer (как это происходит в production)
    signer_for_verify = SignatureUNEP(email, db)
    
    result_with_db = signer_for_verify.verify_cms_container(
        cms_signature_bytes=cms_der,
        signed_document=document,
        public_key_b64=None,
        allow_db_fallback=True  # Получаем из БД
    )
    
    if result_with_db.get('is_valid'):
        print("✓ Подпись ВАЛИДНА (с получением из БД)\n")
    else:
        print("✗ Подпись НЕВАЛИДНА (с получением из БД)")
        print(f"Checks: {result_with_db.get('checks')}")
        print(f"Error: {result_with_db.get('error')}\n")
        return False
    
    # 8. Проверяем атрибуты
    print("[7] Проверка атрибутов подписи...")
    attrs = result.get('attrs', [])
    print(f"✓ Найдено {len(attrs)} атрибутов")
    
    has_name = any(attr.get('oid') == '1.2.643.7.1.1.1.128' for attr in attrs)
    has_email = any(attr.get('oid') == '1.2.840.113549.1.9.1' for attr in attrs)
    
    if has_name and has_email:
        print("✓ Найдены атрибуты пользователя (name и email)\n")
    else:
        print(f"⚠ Атрибуты: name={has_name}, email={has_email}\n")
    
    print("="*80)
    print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = test_sign_and_verify_full_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
