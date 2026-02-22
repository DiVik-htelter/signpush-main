-- ============================================================================
-- SQL Миграция: Создание таблицы для хранения метаданных о подписях
-- ============================================================================
-- Автор: SignPush System
-- Дата: 2026-02-21
-- Описание: Создаёт таблицу document_signatures для хранения информации
--           о визуальных и криптографических подписях документов
-- ============================================================================

-- Создание таблицы для хранения подписей документов
CREATE TABLE IF NOT EXISTS document_signatures (
    -- Уникальный идентификатор подписи
    id SERIAL PRIMARY KEY,
    
    -- Ссылка на подписанный документ (внешний ключ)
    document_id INTEGER NOT NULL,
    
    -- Ссылка на пользователя, который поставил подпись (внешний ключ)
    signer_id INTEGER NOT NULL,
    
    -- Визуальное изображение подписи в формате base64
    -- Это изображение, которое пользователь нарисовал в SignatureModal
    signature_image_base64 TEXT,
    
    -- Криптографическая цифровая подпись (опционально)
    -- Используется для проверки подлинности и целостности документа
    digital_signature TEXT,
    
    -- Метаданные о позиции подписи на странице PDF
    page_number INTEGER NOT NULL DEFAULT 0,
    x_position FLOAT NOT NULL DEFAULT 0,
    y_position FLOAT NOT NULL DEFAULT 0,
    width FLOAT NOT NULL DEFAULT 0,
    height FLOAT NOT NULL DEFAULT 0,
    
    -- Временная метка подписания (автоматически устанавливается при вставке)
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- IP адрес, с которого была поставлена подпись (для аудита)
    ip_address VARCHAR(45),
    
    -- Флаг валидности подписи
    -- Может быть установлен в false, если документ был изменён после подписания
    is_valid BOOLEAN DEFAULT true,
    
    -- Дополнительные метаданные в формате JSON (опционально)
    -- Например: информация о браузере, устройстве, геолокации и т.д.
    metadata JSONB,
    
    -- Внешние ключи с каскадным удалением
    CONSTRAINT fk_document
        FOREIGN KEY(document_id) 
        REFERENCES documents(id)
        ON DELETE CASCADE,
        
    CONSTRAINT fk_signer
        FOREIGN KEY(signer_id) 
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- ============================================================================
-- Создание индексов для оптимизации запросов
-- ============================================================================

-- Индекс для быстрого поиска всех подписей конкретного документа
CREATE INDEX IF NOT EXISTS idx_signatures_document_id 
ON document_signatures(document_id);

-- Индекс для поиска всех подписей конкретного пользователя
CREATE INDEX IF NOT EXISTS idx_signatures_signer_id 
ON document_signatures(signer_id);

-- Индекс для поиска подписей по дате
CREATE INDEX IF NOT EXISTS idx_signatures_signed_at 
ON document_signatures(signed_at DESC);

-- Индекс для фильтрации валидных/невалидных подписей
CREATE INDEX IF NOT EXISTS idx_signatures_is_valid 
ON document_signatures(is_valid);

-- ============================================================================
-- Создание таблицы для версионирования документов (опционально)
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_versions (
    -- Уникальный идентификатор версии
    id SERIAL PRIMARY KEY,
    
    -- Ссылка на оригинальный документ
    original_document_id INTEGER NOT NULL,
    
    -- Номер версии (инкрементируется с каждой новой версией)
    version_number INTEGER NOT NULL DEFAULT 1,
    
    -- Название версии документа
    title VARCHAR(255) NOT NULL,
    
    -- SHA-256 хеш версии документа
    hash VARCHAR(255) NOT NULL,
    
    -- Unix timestamp создания версии
    created_at BIGINT NOT NULL,
    
    -- Содержимое версии документа в base64
    base64 TEXT NOT NULL,
    
    -- ID пользователя, создавшего версию
    created_by INTEGER NOT NULL,
    
    -- Описание изменений в этой версии
    change_description TEXT,
    
    -- Тип изменения: 'signed', 'edited', 'annotated', etc.
    change_type VARCHAR(50) DEFAULT 'signed',
    
    -- Внешние ключи
    CONSTRAINT fk_original_document
        FOREIGN KEY(original_document_id) 
        REFERENCES documents(id)
        ON DELETE CASCADE,
        
    CONSTRAINT fk_created_by
        FOREIGN KEY(created_by) 
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- Индекс для версий конкретного документа
CREATE INDEX IF NOT EXISTS idx_versions_original_doc 
ON document_versions(original_document_id, version_number DESC);

-- ============================================================================
-- Комментарии к таблицам
-- ============================================================================

COMMENT ON TABLE document_signatures IS 'Хранит метаданные о подписях документов';
COMMENT ON TABLE document_versions IS 'Хранит историю версий документов';

COMMENT ON COLUMN document_signatures.signature_image_base64 IS 'Визуальное изображение подписи в base64';
COMMENT ON COLUMN document_signatures.digital_signature IS 'Криптографическая ЭЦП для проверки подлинности';
COMMENT ON COLUMN document_signatures.is_valid IS 'Флаг валидности: false если документ был изменён после подписания';

-- ============================================================================
-- ИНСТРУКЦИЯ ПО ПРИМЕНЕНИЮ МИГРАЦИИ:
-- ============================================================================
-- 
-- 1. Подключитесь к PostgreSQL:
--    psql -U your_username -d your_database_name
--
-- 2. Выполните этот скрипт:
--    \i create_signatures_table.sql
--    или
--    psql -U your_username -d your_database_name -f create_signatures_table.sql
--
-- 3. Проверьте, что таблицы созданы:
--    \dt
--    \d document_signatures
--    \d document_versions
-- ============================================================================

-- Пример проверочных запросов после создания таблиц:

-- Посмотреть все подписи для документа с ID = 1
-- SELECT * FROM document_signatures WHERE document_id = 1;

-- Посмотреть все подписи пользователя
-- SELECT ds.*, d.title 
-- FROM document_signatures ds
-- JOIN documents d ON ds.document_id = d.id
-- WHERE ds.signer_id = (SELECT id FROM users WHERE login = 'admin@gmail.com');

-- Посмотреть все версии документа
-- SELECT * FROM document_versions WHERE original_document_id = 1 ORDER BY version_number DESC;
