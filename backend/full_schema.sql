--
-- PostgreSQL database dump
--

-- Dumped from database version 15.8
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: log_document_activity(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_document_activity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.log_document_activity() OWNER TO postgres;

--
-- Name: log_user_activity(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.log_user_activity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (user_id, action_type, description)
        -- Замените NEW.username на NEW.email или NEW.first_name
        VALUES (NEW.id, 'user_created', 'Создан новый пользователь: ' || NEW.email); 
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (user_id, action_type, description)
        VALUES (NEW.id, 'user_updated', 'Данные пользователя изменены');
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_user_activity() OWNER TO postgres;

--
-- Name: update_document_signing_status(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_document_signing_status() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    has_unep BOOLEAN;
    has_visual BOOLEAN;
    new_status VARCHAR(50);
BEGIN
    -- Отмечаем выполнение задачи в маршруте (если привязано)
    IF NEW.signature_route_id IS NOT NULL THEN
        UPDATE signature_routes 
        SET signature_status = 'signed', 
            signed_at = EXTRACT(EPOCH FROM NOW())::BIGINT
        WHERE id = NEW.signature_route_id;
    END IF;

    -- Проверяем наличие подписей разных типов для этого документа
    SELECT EXISTS (
        SELECT 1 FROM document_signatures 
        WHERE document_id = NEW.document_id AND signature_type = 'digital_unep'
    ) INTO has_unep;

    SELECT EXISTS (
        SELECT 1 FROM document_signatures 
        WHERE document_id = NEW.document_id AND signature_type = 'visual'
    ) INTO has_visual;

    -- Логика определения статуса:
    -- 1. Если есть УНЭП (неважно, есть ли визуальная) -> fully_signed
    -- 2. Если УНЭП нет, но есть визуальная -> partially_signed
    -- 3. В остальных случаях (хотя триггер срабатывает на INSERT) -> unsigned
    IF has_unep THEN
        new_status := 'fully_signed';
    ELSIF has_visual THEN
        new_status := 'partially_signed';
    ELSE
        new_status := 'unsigned';
    END IF;

    -- Обновляем документ
    UPDATE documents 
    SET is_signed = true,
        signing_status = new_status,
        updated_at = EXTRACT(EPOCH FROM NOW())::BIGINT
    WHERE id = NEW.document_id;
    
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_document_signing_status() OWNER TO postgres;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    action_type character varying(100) NOT NULL,
    document_id integer,
    ip_address character varying(45),
    created_at bigint DEFAULT (EXTRACT(epoch FROM now()))::bigint,
    description text,
    status character varying(50) DEFAULT 'success'::character varying,
    error_message text
);


ALTER TABLE public.audit_logs OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_logs_id_seq OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: certificates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.certificates (
    id integer NOT NULL,
    user_id integer NOT NULL,
    certificate_serial_number character varying(255) NOT NULL,
    valid_from bigint NOT NULL,
    valid_to bigint NOT NULL,
    certificate_type character varying(50),
    public_key_pem text,
    is_active boolean DEFAULT true,
    created_at bigint DEFAULT (EXTRACT(epoch FROM CURRENT_TIMESTAMP))::bigint
);


ALTER TABLE public.certificates OWNER TO postgres;

--
-- Name: certificates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.certificates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.certificates_id_seq OWNER TO postgres;

--
-- Name: certificates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.certificates_id_seq OWNED BY public.certificates.id;


--
-- Name: document_signatures; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.document_signatures (
    id integer NOT NULL,
    document_id integer NOT NULL,
    signature_route_id integer,
    signer_id integer NOT NULL,
    signature_image_base64 text NOT NULL,
    page_number integer DEFAULT 0 NOT NULL,
    x_position double precision DEFAULT 0 NOT NULL,
    y_position double precision DEFAULT 0 NOT NULL,
    width double precision DEFAULT 0 NOT NULL,
    height double precision DEFAULT 0 NOT NULL,
    signature_type character varying(50) DEFAULT 'visual'::character varying,
    digital_signature_hash text,
    unep_cipher character varying(255),
    signed_at bigint DEFAULT (EXTRACT(epoch FROM CURRENT_TIMESTAMP))::bigint,
    is_valid boolean DEFAULT true,
    public_key text,
    CONSTRAINT valid_signature_type CHECK (((signature_type)::text = ANY ((ARRAY['visual'::character varying, 'digital_ukey'::character varying, 'digital_unep'::character varying])::text[])))
);


ALTER TABLE public.document_signatures OWNER TO postgres;

--
-- Name: document_signatures_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.document_signatures_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.document_signatures_id_seq OWNER TO postgres;

--
-- Name: document_signatures_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.document_signatures_id_seq OWNED BY public.document_signatures.id;


--
-- Name: document_transfers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.document_transfers (
    id integer NOT NULL,
    document_id integer NOT NULL,
    sent_by_id integer NOT NULL,
    sent_to_id integer NOT NULL,
    transfer_type character varying(50) NOT NULL,
    transfer_status character varying(50) DEFAULT 'sent'::character varying,
    message text,
    sent_at bigint DEFAULT (EXTRACT(epoch FROM CURRENT_TIMESTAMP))::bigint,
    read_at bigint,
    CONSTRAINT valid_transfer_status CHECK (((transfer_status)::text = ANY ((ARRAY['sent'::character varying, 'delivered'::character varying, 'read'::character varying, 'accepted'::character varying, 'rejected'::character varying])::text[]))),
    CONSTRAINT valid_transfer_type CHECK (((transfer_type)::text = ANY ((ARRAY['for_signature'::character varying, 'for_review'::character varying, 'completed'::character varying, 'information'::character varying])::text[])))
);


ALTER TABLE public.document_transfers OWNER TO postgres;

--
-- Name: document_transfers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.document_transfers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.document_transfers_id_seq OWNER TO postgres;

--
-- Name: document_transfers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.document_transfers_id_seq OWNED BY public.document_transfers.id;


--
-- Name: documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    hash character varying(255) NOT NULL,
    base64 text NOT NULL,
    owner_id integer NOT NULL,
    is_signed boolean DEFAULT false,
    signing_status character varying(50) DEFAULT 'unsigned'::character varying,
    document_status character varying(50) DEFAULT 'draft'::character varying,
    created_at bigint DEFAULT (EXTRACT(epoch FROM CURRENT_TIMESTAMP))::bigint,
    updated_at bigint DEFAULT (EXTRACT(epoch FROM CURRENT_TIMESTAMP))::bigint,
    mime_type character varying(50) DEFAULT 'application/pdf'::character varying,
    CONSTRAINT valid_document_status CHECK (((document_status)::text = ANY ((ARRAY['draft'::character varying, 'sent'::character varying, 'in_progress'::character varying, 'completed'::character varying, 'archived'::character varying])::text[]))),
    CONSTRAINT valid_signing_status CHECK (((signing_status)::text = ANY ((ARRAY['unsigned'::character varying, 'partially_signed'::character varying, 'fully_signed'::character varying, 'rejected'::character varying])::text[])))
);


ALTER TABLE public.documents OWNER TO postgres;

--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.documents_id_seq OWNER TO postgres;

--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- Name: signature_routes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.signature_routes (
    id integer NOT NULL,
    document_id integer NOT NULL,
    required_signer_id integer NOT NULL,
    order_index integer NOT NULL,
    signature_status character varying(50) DEFAULT 'pending'::character varying,
    signature_note character varying(255),
    signed_at bigint,
    deadline_at bigint,
    CONSTRAINT valid_signature_status CHECK (((signature_status)::text = ANY ((ARRAY['pending'::character varying, 'signed'::character varying, 'rejected'::character varying, 'skipped'::character varying])::text[])))
);


ALTER TABLE public.signature_routes OWNER TO postgres;

--
-- Name: signature_routes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.signature_routes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.signature_routes_id_seq OWNER TO postgres;

--
-- Name: signature_routes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.signature_routes_id_seq OWNED BY public.signature_routes.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    first_name character varying(100),
    last_name character varying(100),
    is_email_verified boolean DEFAULT false,
    private_key text,
    public_key text,
    created_at bigint DEFAULT (EXTRACT(epoch FROM CURRENT_TIMESTAMP))::bigint,
    updated_at bigint DEFAULT (EXTRACT(epoch FROM CURRENT_TIMESTAMP))::bigint,
    is_active boolean DEFAULT true
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: certificates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.certificates ALTER COLUMN id SET DEFAULT nextval('public.certificates_id_seq'::regclass);


--
-- Name: document_signatures id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_signatures ALTER COLUMN id SET DEFAULT nextval('public.document_signatures_id_seq'::regclass);


--
-- Name: document_transfers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_transfers ALTER COLUMN id SET DEFAULT nextval('public.document_transfers_id_seq'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- Name: signature_routes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.signature_routes ALTER COLUMN id SET DEFAULT nextval('public.signature_routes_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: certificates certificates_certificate_serial_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_certificate_serial_number_key UNIQUE (certificate_serial_number);


--
-- Name: certificates certificates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_pkey PRIMARY KEY (id);


--
-- Name: document_signatures document_signatures_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_signatures
    ADD CONSTRAINT document_signatures_pkey PRIMARY KEY (id);


--
-- Name: document_transfers document_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_transfers
    ADD CONSTRAINT document_transfers_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: signature_routes signature_routes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.signature_routes
    ADD CONSTRAINT signature_routes_pkey PRIMARY KEY (id);


--
-- Name: signature_routes unique_route_per_doc_signer; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.signature_routes
    ADD CONSTRAINT unique_route_per_doc_signer UNIQUE (document_id, required_signer_id, order_index);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_document_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_document_id ON public.audit_logs USING btree (document_id);


--
-- Name: idx_audit_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: idx_documents_owner_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_owner_id ON public.documents USING btree (owner_id);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: documents trg_audit_docs; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_docs AFTER INSERT OR DELETE OR UPDATE ON public.documents FOR EACH ROW EXECUTE FUNCTION public.log_document_activity();


--
-- Name: users trg_audit_users; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_audit_users AFTER INSERT OR UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.log_user_activity();


--
-- Name: document_signatures trg_signature_added; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_signature_added AFTER INSERT ON public.document_signatures FOR EACH ROW EXECUTE FUNCTION public.update_document_signing_status();


--
-- Name: documents trg_update_docs; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_docs BEFORE UPDATE ON public.documents FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users trg_update_users; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_update_users BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: certificates certificates_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: document_signatures document_signatures_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_signatures
    ADD CONSTRAINT document_signatures_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: document_signatures document_signatures_signature_route_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_signatures
    ADD CONSTRAINT document_signatures_signature_route_id_fkey FOREIGN KEY (signature_route_id) REFERENCES public.signature_routes(id) ON DELETE SET NULL;


--
-- Name: document_signatures document_signatures_signer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_signatures
    ADD CONSTRAINT document_signatures_signer_id_fkey FOREIGN KEY (signer_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: document_transfers document_transfers_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_transfers
    ADD CONSTRAINT document_transfers_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: document_transfers document_transfers_sent_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_transfers
    ADD CONSTRAINT document_transfers_sent_by_id_fkey FOREIGN KEY (sent_by_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: document_transfers document_transfers_sent_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_transfers
    ADD CONSTRAINT document_transfers_sent_to_id_fkey FOREIGN KEY (sent_to_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: documents documents_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: signature_routes signature_routes_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.signature_routes
    ADD CONSTRAINT signature_routes_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: signature_routes signature_routes_required_signer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.signature_routes
    ADD CONSTRAINT signature_routes_required_signer_id_fkey FOREIGN KEY (required_signer_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

