-- ============================================================================
-- СХЕМА БД SignPush (MVP) 
-- ============================================================================

-- 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    
    is_email_verified BOOLEAN DEFAULT false,
    
    private_key TEXT,
    public_key TEXT
    
    created_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT),
    updated_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. ТАБЛИЦА ДОКУМЕНТОВ
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    hash VARCHAR(255) NOT NULL,
    base64 TEXT NOT NULL, 
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    is_signed BOOLEAN DEFAULT false, -- обновляется триггером
    signing_status VARCHAR(50) DEFAULT 'unsigned',  -- обновляется триггером
    document_status VARCHAR(50) DEFAULT 'draft',
    
    created_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT),
    updated_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT),
    mime_type VARCHAR(50) DEFAULT 'application/pdf',
    
    CONSTRAINT valid_signing_status CHECK (signing_status IN ('unsigned', 'partially_signed', 'fully_signed', 'rejected')),
    CONSTRAINT valid_document_status CHECK (document_status IN ('draft', 'sent', 'in_progress', 'completed', 'archived', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_documents_owner_id ON documents(owner_id);


-- 3. МАРШРУТЫ ПОДПИСЕЙ
CREATE TABLE IF NOT EXISTS signature_routes (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    required_signer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    signature_status VARCHAR(50) DEFAULT 'pending',
    signature_note VARCHAR(255),
    signed_at BIGINT,
    deadline_at BIGINT,
    
    CONSTRAINT valid_signature_status CHECK (signature_status IN ('pending', 'signed', 'rejected', 'skipped')),
    CONSTRAINT unique_route_per_doc_signer UNIQUE(document_id, required_signer_id, order_index)
);

-- модернизировать таблицу под графическую и унэп подписи
-- 4. ТАБЛИЦА ПОДПИСЕЙ
CREATE TABLE IF NOT EXISTS document_signatures (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    signature_route_id INTEGER REFERENCES signature_routes(id) ON DELETE SET NULL,
    signer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    signature_image_base64 TEXT NOT NULL,
    
    page_number INTEGER NOT NULL DEFAULT 0,
    x_position FLOAT NOT NULL DEFAULT 0,
    y_position FLOAT NOT NULL DEFAULT 0,
    width FLOAT NOT NULL DEFAULT 0,
    height FLOAT NOT NULL DEFAULT 0,
    
    signature_type VARCHAR(50) DEFAULT 'visual', 
    digital_signature_hash TEXT,
    unep_cipher VARCHAR(255),
    public_key TEXT,

    signed_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT),
    is_valid BOOLEAN DEFAULT true,
    
    CONSTRAINT valid_signature_type CHECK (signature_type IN ('visual', 'digital_unep', 'digital_ukey'))
);

-- 5. ПЕРЕСЫЛКА ДОКУМЕНТОВ
CREATE TABLE IF NOT EXISTS document_transfers (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    sent_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sent_to_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    transfer_type VARCHAR(50) NOT NULL, 
    transfer_status VARCHAR(50) DEFAULT 'sent',
    message TEXT,
    
    sent_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT),
    read_at BIGINT,
    
    CONSTRAINT valid_transfer_type CHECK (transfer_type IN ('for_signature', 'for_review', 'completed', 'information')),
    CONSTRAINT valid_transfer_status CHECK (transfer_status IN ('sent', 'delivered', 'read', 'accepted', 'rejected'))
);

-- 6. ЛОГИ АУДИТА
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    -- Убираем REFERENCES, чтобы ID не обнулялся при удалении пользователя
    user_id INTEGER, 
    action_type VARCHAR(100) NOT NULL,
    -- Убираем REFERENCES, чтобы ID документа сохранялся для истории
    document_id INTEGER, 
    ip_address VARCHAR(45),
    created_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT),
    description TEXT,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT
);

-- Индексы для быстрого поиска по логам (теперь они особенно важны)
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_document_id ON audit_logs(document_id);

-- 7. СЕРТИФИКАТЫ
CREATE TABLE IF NOT EXISTS certificates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    certificate_serial_number VARCHAR(255) NOT NULL UNIQUE,
    valid_from BIGINT NOT NULL,
    valid_to BIGINT NOT NULL,
    certificate_type VARCHAR(50), 
    public_key_pem TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT)
);

-- ============================================================================
-- ПРЕДСТАВЛЕНИЯ (VIEWS)
-- ============================================================================

CREATE OR REPLACE VIEW signature_tasks_view AS
SELECT 
    sr.id as route_id, d.id as document_id, d.title,
    sr.required_signer_id as signer_id, sr.signature_status,
    sr.order_index, sr.deadline_at
FROM signature_routes sr
JOIN documents d ON sr.document_id = d.id
WHERE sr.signature_status = 'pending';

-- ============================================================================
-- ФУНКЦИИ ТРИГГЕРОВ (ОБНОВЛЕННЫЕ ПОД BIGINT)
-- ============================================================================

-- 1. Универсальный updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = EXTRACT(EPOCH FROM NOW())::BIGINT;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_docs BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_update_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 2. Логика подписания (статусы документа и маршрута)
CREATE OR REPLACE FUNCTION update_document_signing_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Помечаем задачу в маршруте как выполненную
    UPDATE signature_routes 
    SET signature_status = 'signed', 
        signed_at = EXTRACT(EPOCH FROM NOW())::BIGINT
    WHERE id = NEW.signature_route_id;

    -- Обновляем статус самого документа
    UPDATE documents 
    SET is_signed = true,
        signing_status = CASE 
            WHEN (SELECT COUNT(*) FROM signature_routes WHERE document_id = NEW.document_id AND signature_status = 'pending') = 0 
            THEN 'fully_signed'
            ELSE 'partially_signed'
        END
    WHERE id = NEW.document_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_signature_added AFTER INSERT ON document_signatures FOR EACH ROW EXECUTE FUNCTION update_document_signing_status();

-- 3. Автоматический аудит действий
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (user_id, action_type, description)
        VALUES (NEW.id, 'user_created', 'Создан новый пользователь: ' || NEW.email);
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (user_id, action_type, description)
        VALUES (NEW.id, 'user_updated', 'Данные пользователя изменены');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер на создание и обновление пользователя
CREATE TRIGGER trg_audit_users
AFTER INSERT OR UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION log_user_activity();

CREATE OR REPLACE FUNCTION log_document_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- 1. Создание документа
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (user_id, action_type, document_id, description)
        VALUES (NEW.owner_id, 'document_created', NEW.id, 'Документ загружен: ' || NEW.title);
        RETURN NEW;

    -- 2. Изменение (подписание) документа
    ELSIF (TG_OP = 'UPDATE') THEN
        IF (OLD.signing_status != NEW.signing_status AND NEW.signing_status = 'fully_signed') THEN
            INSERT INTO audit_logs (user_id, action_type, document_id, description)
            VALUES (NEW.owner_id, 'document_fully_signed', NEW.id, 'Завершено подписание документа');
        END IF;
        RETURN NEW;

    -- 3. Удаление документа
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_logs (user_id, action_type, document_id, description)
        VALUES (OLD.owner_id, 'document_deleted', OLD.id, 'Документ удален: ' || OLD.title);
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Обновляем сам триггер, добавив событие DELETE
DROP TRIGGER IF EXISTS trg_audit_docs ON documents;
CREATE TRIGGER trg_audit_docs 
AFTER INSERT OR UPDATE OR DELETE ON documents 
FOR EACH ROW EXECUTE FUNCTION log_document_activity();

-- 4. Защита от подписания закрытых документов
CREATE OR REPLACE FUNCTION prevent_signing_closed_docs()
RETURNS TRIGGER AS $$
DECLARE doc_status VARCHAR;
BEGIN
    SELECT document_status INTO doc_status FROM documents WHERE id = NEW.document_id;
    IF doc_status IN ('archived', 'rejected') THEN
        RAISE EXCEPTION 'Нельзя подписать документ в статусе %', doc_status;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_doc_before_sign BEFORE INSERT ON document_signatures FOR EACH ROW EXECUTE FUNCTION prevent_signing_closed_docs();

-- 5. Синхронизация профиля пользователя с сертификатом
CREATE OR REPLACE FUNCTION sync_user_cert_info()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users 
    SET certificate_serial_number = NEW.certificate_serial_number,
        certificate_expires_at = NEW.valid_to
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_cert AFTER INSERT ON certificates FOR EACH ROW EXECUTE FUNCTION sync_user_cert_info();