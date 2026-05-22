#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы CMS контейнера с информацией о пользователе
"""
import sys
import os
import base64
import logging
from datetime import datetime

# Добавляем текущую директорию в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service import SignatureUNEP
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def test_cms_with_user_attributes():
    """Тестирует создание и проверку CMS контейнера с атрибутами пользователя"""
    
    print("\n" + "="*80)
    print("ТЕСТ: Подписание документа с информацией о пользователе")
    print("="*80 + "\n")
    
    # Инициализируем БД (используя mock для теста)
    db = Database()
    email = "test.user@example.com"
    
    print(f"[1] Инициализация подписанта: {email}")
    signer = SignatureUNEP(email, db)
    
    # Генерируем ключи
    print("[2] Генерация ключевой пары...")
    keys = signer.generate_user_keys()
    if not keys:
        print("✗ Ошибка при генерации ключей")
        return False
    
    public_key_b64, private_key_b64 = keys
    print(f"✓ Ключи сгенерированы")
    print(f"  - Публичный ключ (base64): {public_key_b64[:50]}...")
    print(f"  - Приватный ключ (base64): {private_key_b64[:50]}...")
    
    # Информация о пользователе
    user_info = {
        'first_name': 'Иван',
        'last_name': 'Петров',
        'email': email
    }
    print(f"\n[3] Информация о пользователе:")
    print(f"  - Имя: {user_info['first_name']} {user_info['last_name']}")
    print(f"  - Email: {user_info['email']}")
    
    # Документ для подписи
    test_document = "Это тестовый документ для подписания"
    print(f"\n[4] Подписываемый документ:")
    print(f"  - Содержимое: {test_document}")
    
    # Подписываем документ
    print(f"\n[5] Подписание документа...")
    try:
        signed_payload = signer.signed_hash(test_document, private_key_b64, user_info=user_info)
        print("✓ Документ успешно подписан")
    except Exception as e:
        print(f"✗ Ошибка при подписании: {e}")
        return False
    
    # Создаем CMS контейнер
    print(f"\n[6] Создание CMS контейнера...")
    try:
        doc_hash = signer.hash_document(test_doc)
        cms_der = signer.create_cms_container(
            document_hash=doc_hash,
            private_key_b64=private_key_b64,
            public_key_b64=public_key_b64,
            user_info=user_info,
            output_filename="test_document.sig"
        )
        print(f"✓ CMS контейнер создан")
        print(f"  - Размер: {len(cms_der)} байт")
    except Exception as e:
        print(f"✗ Ошибка при создании CMS контейнера: {e}")
        return False
    
    # Проверяем подпись
    print(f"\n[7] Проверка подписи...")
    try:
        verify_result = signer.verify_cms_container(
            cms_signature_bytes=cms_der,
            signed_document=test_document,
            public_key_b64=public_key_b64,
            allow_db_fallback=False
        )
    except Exception as e:
        print(f"✗ Ошибка при проверке подписи: {e}")
        return False
    
    print(f"✓ Подпись проверена")
    print(f"  - Результат валидации: {verify_result['is_valid']}")
    print(f"  - Проверки:")
    for check_name, check_result in verify_result['checks'].items():
        status = "✓" if check_result else "✗"
        print(f"    {status} {check_name}: {check_result}")
    
    # Выводим атрибуты подписи
    print(f"\n[8] Атрибуты подписи (signedAttrs):")
    print(f"  - Всего атрибутов: {len(verify_result['attrs'])}")
    print("\n  Содержимое:")
    for attr in verify_result['attrs']:
        print(f"    • {attr['name']} (OID: {attr['oid']})")
        for val in attr['values']:
            if isinstance(val, dict) and 'value' in val:
                print(f"      └─ {val['type']}: {val['value']}")
            else:
                print(f"      └─ {val}")
    
    # Проверяем, что информация о пользователе присутствует
    print(f"\n[9] Поиск информации о пользователе в атрибутах:")
    
    found_user_data = {}
    for attr in verify_result['attrs']:
        if attr['oid'] == '1.2.643.7.1.1.1.128':  # Имя подписанта
            if attr['values']:
                found_user_data['name'] = attr['values'][0].get('value', 'N/A')
        elif attr['oid'] == '1.2.840.113549.1.9.1':  # Email
            if attr['values']:
                found_user_data['email'] = attr['values'][0].get('value', 'N/A')
    
    if found_user_data.get('name'):
        print(f"  ✓ Имя подписанта найдено: {found_user_data['name']}")
    else:
        print(f"  ✗ Имя подписанта не найдено")
    
    if found_user_data.get('email'):
        print(f"  ✓ Email подписанта найден: {found_user_data['email']}")
    else:
        print(f"  ✗ Email подписанта не найден")
    
    # Проверяем, что нет кастомного OID для встроенного ключа
    print(f"\n[10] Проверка на наличие кастомного OID:")
    custom_oid = '1.2.643.7.1.0.99999.1'
    custom_oid_found = any(attr['oid'] == custom_oid for attr in verify_result['attrs'])
    if not custom_oid_found:
        print(f"  ✓ Кастомный OID {custom_oid} не найден (как и ожидалось)")
    else:
        print(f"  ✗ Кастомный OID {custom_oid} всё ещё присутствует!")
    
    print("\n" + "="*80)
    if verify_result['is_valid'] and found_user_data.get('name') and found_user_data.get('email'):
        print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        print("✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        return False
    
if __name__ == "__main__":
    try:
        success = test_cms_with_user_attributes()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")
        logging.exception("Exception occurred:")
        sys.exit(1)
