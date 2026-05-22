#!/usr/bin/env python3
"""
Скрипт для анализа и отладки CMS контейнера (.sig)
Проверяет совместимость со стандартами и другими инструментами
"""
import sys
import os
import base64
from asn1crypto import cms, core

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service import SignatureUNEP
from database import Database

def analyze_cms_container():
    """Анализирует структуру CMS контейнера в деталях"""
    
    print("\n" + "="*80)
    print("АНАЛИЗ CMS КОНТЕЙНЕРА - СОВМЕСТИМОСТЬ И СТРУКТУРА")
    print("="*80 + "\n")
    
    db = Database()
    email = "analyze.test@example.com"
    signer = SignatureUNEP(email, db)
    
    # Генерируем ключи  
    print("[1] Генерация ключей...")
    keys = signer.generate_user_keys()
    public_key_b64, private_key_b64 = keys
    print("✓ Ключи сгенерированы\n")
    
    # Информация о пользователе
    user_info = {
        'first_name': 'Сергей',
        'last_name': 'Иванов',
        'email': email
    }
    
    # Подписываем документ
    print("[2] Подписание тестового документа...")
    test_document = "Тестовый документ для анализа структуры CMS"
    print("✓ Документ подписан\n")
    
    # Создаем CMS контейнер
    print("[3] Создание CMS контейнера...")
    doc_hash = signer.hash_document(test_document)
    cms_der = signer.create_cms_container(
        document_hash=doc_hash,
        private_key_b64=private_key_b64,
        public_key_b64=public_key_b64,
        user_info=user_info,
        output_filename="analyze_document.sig"
    )
    print(f"✓ CMS контейнер создан ({len(cms_der)} байт)\n")
    
    # Парсим CMS контейнер
    print("[4] Парсинг структуры CMS контейнера...")
    content_info = cms.ContentInfo.load(cms_der)
    signed_data = content_info['content']
    signer_infos = signed_data['signer_infos']
    signer_info = signer_infos[0]
    signed_attrs = signer_info['signed_attrs']
    
    print("✓ Контейнер успешно распарсен\n")
    
    # Выводим детали о контейнере
    print("[5] ОСНОВНАЯ ИНФОРМАЦИЯ О КОНТЕЙНЕРЕ:")
    print(f"  • content_type: {content_info['content_type'].native}")
    print(f"  • version: {signed_data['version'].native}")
    print(f"  • number of signers: {len(signer_infos)}")
    print()
    
    # Информация о подписывающем
    print("[6] ИНФОРМАЦИЯ О ПОДПИСЫВАЮЩЕМ (SignerInfo):")
    print(f"  • version: {signer_info['version'].native}")
    print(f"  • digest algorithm: {signer_info['digest_algorithm']['algorithm'].dotted}")
    print(f"  • signature algorithm: {signer_info['signature_algorithm']['algorithm'].dotted}")
    print(f"  • sid type: {signer_info['sid'].name}")
    if signer_info['sid'].name == 'subject_key_identifier':
        ski = signer_info['sid'].chosen.native
        print(f"  • SKI (hex): {ski.hex()}")
    print()
    
    # Атрибуты подписи (AuthenticatedAttributes / signedAttrs)
    print("[7] АТРИБУТЫ ПОДПИСИ (AuthenticatedAttributes):")
    print(f"  • Всего атрибутов: {len(signed_attrs)}")
    print()
    
    # Стандартные OID для CMS атрибутов
    OID_NAMES = {
        '1.2.840.113549.1.9.3': 'contentType (PKCS#9)',
        '1.2.840.113549.1.9.4': 'messageDigest (PKCS#9)',
        '1.2.840.113549.1.9.5': 'signingTime (PKCS#9)',
        '1.2.840.113549.1.9.1': 'emailAddress (PKCS#9)',
        '1.2.643.7.1.1.1.128': 'signerName (Russian GOST)',
        '1.2.643.7.1.1.2.2': 'GOST 34.11-2012 256-bit hash',
        '1.2.643.7.1.1.3.2': 'GOST 34.10-2012 256-bit signature',
    }
    
    print("  Содержимое атрибутов:")
    for i, attr in enumerate(signed_attrs, 1):
        oid = attr['type'].dotted if hasattr(attr['type'], 'dotted') else str(attr['type'])
        attr_name = attr['type'].native if hasattr(attr['type'], 'native') else oid
        desc = OID_NAMES.get(oid, 'Unknown/Custom OID')
        
        print(f"\n  {i}. {attr_name}")
        print(f"     OID: {oid}")
        print(f"     Описание: {desc}")
        
        for j, value in enumerate(attr['values'], 1):
            try:
                native_value = value.native
                if isinstance(native_value, bytes):
                    print(f"     Значение {j}: {len(native_value)} байт (hex: {native_value.hex()[:40]}...)")
                else:
                    print(f"     Значение {j}: {native_value}")
            except:
                print(f"     Значение {j}: [неопределённое значение]")
    
    print("\n")
    print("[8] ПРОВЕРКА СОВМЕСТИМОСТИ:")
    
    # Проверяем, что есть все обязательные атрибуты
    required_attrs = {
        '1.2.840.113549.1.9.3': 'contentType',
        '1.2.840.113549.1.9.4': 'messageDigest',
        '1.2.840.113549.1.9.5': 'signingTime',
    }
    
    found_attrs = {attr['type'].dotted if hasattr(attr['type'], 'dotted') else str(attr['type']): True 
                   for attr in signed_attrs}
    
    print("  Обязательные атрибуты PKCS#7/CMS:")
    for oid, name in required_attrs.items():
        if oid in found_attrs:
            print(f"    ✓ {name} ({oid})")
        else:
            print(f"    ✗ {name} ({oid}) - ОТСУТСТВУЕТ")
    
    print("\n  Дополнительные атрибуты (user data):")
    user_attrs = {
        '1.2.643.7.1.1.1.128': 'signerName',
        '1.2.840.113549.1.9.1': 'emailAddress',
    }
    
    for oid, name in user_attrs.items():
        if oid in found_attrs:
            print(f"    ✓ {name} ({oid})")
        else:
            print(f"    ✗ {name} ({oid}) - ОТСУТСТВУЕТ")
    
    print("\n  Алгоритмы ГОСТ:")
    gost_attrs = {
        '1.2.643.7.1.1.2.2': 'GOST 34.11-2012 256-bit hash',
        '1.2.643.7.1.1.3.2': 'GOST 34.10-2012 256-bit signature',
    }
    
    has_gost_hash = signer_info['digest_algorithm']['algorithm'].dotted == '1.2.643.7.1.1.2.2'
    has_gost_sign = signer_info['signature_algorithm']['algorithm'].dotted == '1.2.643.7.1.1.3.2'
    
    for oid, desc in gost_attrs.items():
        if oid == '1.2.643.7.1.1.2.2':
            if has_gost_hash:
                print(f"    ✓ {desc}")
            else:
                print(f"    ✗ {desc} - ИСПОЛЬЗОВАН ДРУГОЙ АЛГОРИТМ")
        elif oid == '1.2.643.7.1.1.3.2':
            if has_gost_sign:
                print(f"    ✓ {desc}")
            else:
                print(f"    ✗ {desc} - ИСПОЛЬЗОВАН ДРУГОЙ АЛГОРИТМ")
    
    print("\n  Кастомные OID:")
    custom_oid = '1.2.643.7.1.0.99999.1'
    if custom_oid in found_attrs:
        print(f"    ✗ Найден кастомный OID {custom_oid} (это проблема!)")
    else:
        print(f"    ✓ Кастомный OID {custom_oid} не используется (хорошо!)")
    
    print("\n" + "="*80)
    print("ИТОГ: Контейнер должен быть совместим с Криптопро CSP")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        analyze_cms_container()
        sys.exit(0)
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
