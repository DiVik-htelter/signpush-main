# 📋 SignPush - Веб-приложение для управления и подписания документов

**SignPush** — полнофункциональное веб-приложение для управления электронными PDF-документами с поддержкой цифрового подписания. Быстрая загрузка, просмотр, подписание и верификация документов.

### ⚡ Быстрый старт
- 🐳 **Docker**: `docker-compose up -d` — развертывание всех сервисов за 2 минуты
- 💻 **Локально**: `npm install && npm start` (frontend) + `pip install -r requirements.txt && python main.py` (backend) и стандартный образ контейнера redis:latest в докере, nginx не обязателен

---

## Основные возможности

- ✅ **Аутентификация** - Безопасная авторизация пользователей через email/password
- ✅ **Управление документами** - Загрузка, просмотр, отправка и фильтрация PDF-файлов
- ✅ **Цифровые подписи** - Создание рукописных подписей прямо в браузере
- ✅ **Подпись УНЭП (ГОСТ)** - Формирование CMS/PKCS#7 подписи для PDF-документов
- ✅ **Проверка подписи УНЭП** - Валидация подписи по встроенному в attrs публичному ключу
- ✅ **Интеграция со сторонними сервисами** - Приём документов на подпись и callback возврат подписанного результата
- ✅ **Размещение подписей** - Удобное размещение подписей на нужных страницах документа
- ✅ **Верификация** - Вычисление SHA-256 хеша для проверки целостности
- ✅ **Пагинация** - Удобная навигация по спискам документов
- ✅ **Профиль пользователя** - Просмотр и редактирование информации профиля
- ✅ **Боковая панель навигации** - Адаптивная боковая панель с функцией сворачивания на десктопе
- ✅ **Отзывчивый дизайн** - Полная поддержка мобильных устройств и десктопа

---

## Технологический стек

### Frontend
- **React** 18.2.0 — современная JavaScript библиотека
- **React Router** v6 — клиентская маршрутизация
- **Bootstrap** 5.3.2 + React-Bootstrap — адаптивный UI фреймворк
- **PDF.js** 3.10.111 — рендеринг и работа с PDF
- **Axios** 1.5.1 — HTTP клиент для API запросов
- **React Context API** — управление состоянием приложения
- **luxon** — работа с датами и временем
- **jssha** — вычисление хешей SHA-256

### Backend
- **FastAPI** 0.104.1 — современный асинхронный веб-фреймворк
- **Uvicorn** 0.24.0 — ASGI сервер
- **Pydantic** 2.5.0 — валидация данных
- **PostgreSQL** — база данных для хранения документов и пользователей
- **psycopg2-binary** 2.9.9 — драйвер PostgreSQL
- **gostcrypto** 1.2.5 — криптография ГОСТ (УНЭП)
- **asn1crypto** 1.5.1 — сборка/разбор CMS(PKCS#7) подписи
- **PyMuPDF (fitz)** 1.23.8 — обработка и редактирование PDF
- **Pillow** 10.1.0 — обработка изображений
- **Python** 3.8+ — язык программирования

### Frontend зависимости
```json
{
  "react": "^18.2.0",
  "react-bootstrap": "^2.9.0",
  "bootstrap": "^5.3.2",
  "axios": "^1.5.1",
  "pdfjs-dist": "^3.10.111",
  "react-pdf": "^7.3.3",
  "react-signature-canvas": "^1.0.6",
  "react-cookie": "^6.1.1"
}
```

---

## 📂 Структура проекта

```
signpush-main/
├── 📁 src/                          # Исходный код React приложения
│   ├── 📁 components/               # Переиспользуемые компоненты UI
│   │   ├── header/                  # Заголовок с логотипом
│   │   ├── sidebar/                 # Боковая панель навигации (с функцией сворачивания)
│   │   ├── pdf-reader/              # Просмотр PDF документов
│   │   ├── pdf-documents/           # Список документов
│   │   ├── paginator/               # Компонент пагинации
│   │   ├── signature-modal/         # Модальное окно подписи
│   │   ├── detect-os/               # Детектирование ОС
│   │   └── require-auth/            # Защита авторизованного контента
│   ├── 📁 pages/                    # Страницы приложения
│   │   ├── home/                    # Главная страница
│   │   ├── documents/               # Страница с документами (deprecated)
│   │   ├── my-documents/            # Страница со списком документов пользователя
│   │   ├── upload/                  # Страница загрузки документов
│   │   ├── send-document/           # Страница отправки документов другим пользователям
│   │   ├── signature-verification/  # Страница проверки УНЭП подписи
│   │   ├── profile/                 # Страница профиля пользователя
│   │   ├── settings/                # Страница настроек
│   │   ├── login/                   # Страница входа
│   │   ├── registration/            # Страница регистрации
│   │   └── layout/                  # Главный layout приложения
│   ├── 📁 context/                  # React Context (управление состоянием)
│   │   ├── AuthProvider.js          # Контекст аутентификации
│   │   └── SidebarContext.js        # Контекст состояния боковой панели
│   ├── 📁 hooks/                    # Кастомные React хуки
│   │   └── useAuth.js               # Хук для работы с аутентификацией
│   ├── 📁 api/                      # API интеграция
│   │   └── axios.js                 # Конфигурация HTTP клиента
│   ├── 📁 styles/                   # Глобальные стили
│   │   └── mobile.css               # Мобильные стили
│   ├── 📁 fonts/                    # Шрифты приложения
│   ├── App.js                       # Главный компонент приложения
│   ├── index.js                     # Точка входа React
│   └── index.css                    # Глобальные CSS стили
│
├── 📁 public/                       # Статические файлы и HTML
│   ├── index.html                   # HTML шаблон
│   ├── manifest.json                # PWA манифест
│   └── 📁 pdfjs-dist/               # PDF.js библиотеки (разные версии)
│
├── 📁 backend/                      # Python backend код
│   ├── main.py                      # Точка входа FastAPI приложения
│   ├── database.py                  # Работа с БД
│   ├── config_db.py                 # Конфигурация базы данных
│   ├── pdf_signer.py                # Логика подписания PDF
│   ├── service.py                   # Бизнес-логика и работа с пользователями
│   ├── response_request_classes.py  # Pydantic модели для запросов/ответов API
│   ├── test.py                      # Тесты
│   ├── requirements.txt             # Зависимости Python
│   ├── .env                         # Переменные окружения (NOT в репозитории)
│   ├── Dockerfile                   # Docker конфигурация backend
│   └── full_schema.sql              # SQL схема для базы данных
│
├── 📁 docs/                         # Документация проекта
│   ├── AUTH_STATUS_CHECK_IMPLENTATION.md    # Реализация проверки статуса аутентификации
│   ├── AXIOS_AUTO_HEADERS.md                # Интерцептор для добавления токена в заголовки
│   └── THIRD_PARTY_CALLBACK_API.md         # Интеграция API для 1С и внешних сервисов
│
├── 📁 nginx/                        # Nginx конфигурация для production
│   ├── default.conf                 # Production конфигурация
│   └── Dockerfile                   # Docker образ Nginx
│
├── 📁 nginx-dev/                    # Nginx конфигурация для разработки
│   ├── default.conf
│   └── Dockerfile
│
├── 📁 build/                        # Собранное production приложение (результат npm build)
│
├── .env                             # Переменные окружения проекта (NOT в репозитории)
├── .env.example                     # Пример .env файла для разработки
├── .gitignore                       # Git исключения (включает .env)
├── docker-compose.yml               # Конфигурация Docker Compose
├── Dockerfile                       # Docker образ для основного сервиса
├── deploy.sh                        # Скрипт для развертывания
├── package.json                     # Зависимости и скрипты npm
├── package-lock.json                # Блокировка версий npm зависимостей
├── README.md                        # Этот файл
├── DEPLOYMENT_GUIDE.md              # Подробное руководство развертывания
├── PRE_DEPLOYMENT_CHECKLIST.md      # Чеклист перед развертыванием
└── MOBILE_GUIDE.md                  # Руководство для мобильных устройств
```


### Требования
- **Node.js** >= 14.0
- **npm** >= 6.0
- **Python** >= 3.8 (для backend)
- **PostgreSQL** >= 12 (для базы данных)
- **Redis** (для кэширования и сессий)
- **Docker** и **Docker Compose** (для контейнеризации и развертывания)

---

## 🐳 Docker и Развертывание

Проект полностью готов к развертыванию с использованием **Docker** и **Docker Compose**. Все сервисы (Frontend, Backend, PostgreSQL, Redis, Nginx) упакованы в контейнеры для быстрого и надежного развертывания.

### Быстрый старт через Docker Compose

1. **Убедитесь, что установлены Docker и Docker Compose:**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Переименуйте или скопируйте файл окружения:**
   ```bash
   cp .env.example .env  # если есть пример
   # или отредактируйте существующий .env файл
   ```

3. **Запустите все сервисы:**
   ```bash
   docker-compose up -d
   ```

4. **Остановка сервисов:**
   ```bash
   docker-compose down
   ```

5. **Просмотр логов:**
   ```bash
   docker-compose logs -f backend   # логи backend
   docker-compose logs -f db        # логи базы данных
   docker-compose logs -f redis     # логи Redis
   ```

### Сервисы Docker Compose

| Сервис | Image | Порты | Описание |
|--------|-------|-------|---------|
| **db** | postgres:15-alpine | 5432 | PostgreSQL база данных |
| **redis** | redis:alpine | 6379 | Redis для кэширования |
| **backend** | Custom (./backend) | 8000 | FastAPI backend сервер |
| **nginx** | Custom (./nginx) | 80, 443 | Nginx обратный прокси и сервер статики |

---

## 🔧 Конфигурация через переменные окружения (.env)

Проект использует файлы `.env` для конфигурации подключения к базе данных и Redis. Эти файлы содержат чувствительные данные и **не должны коммититься в репозиторий**.

### Основной .env файл (корневой каталог)

```env
# PostgreSQL Database Configuration
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=signpush
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=false
```

### Backend .env файл (backend/.env)

```env
# Database
DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5432/signpush

# Redis
REDIS_URL=redis://localhost:6379/0

# FastAPI
API_TITLE=SignPush API
API_VERSION=1.0.0

# Security
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost", "https://yourdomain.com"]

# Email Configuration (если используется)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your_app_password
```

### Структура окружения при запуске через Docker Compose

При использовании Docker Compose переменные из `.env` автоматически:
- Передаются в контейнер PostgreSQL для инициализации БД
- Используются backend сервисом для подключения к БД и Redis
- Доступны для других сервисов через `env_file` директиву

### Важно!

⚠️ **Никогда не коммитьте `.env` файлы с реальными паролями!**

- Добавлены в `.gitignore`
- Для разработки используйте локальные значения
- В production используйте безопасные управление секретами (e.g., Docker Secrets, AWS Secrets Manager)
- Создавайте примеры файлов (`.env.example`) без чувствительных данных

---

## 🚀 Локальное развертывание (для разработки)

Для локальной разработки без Docker выполните следующие шаги:

### Backend Setup

1. **Установите зависимости Python:**
   ```bash
   cd backend
   python -m venv venv
   # Для Windows:
   venv\Scripts\activate
   # Для Linux/macOS:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

2. **Создайте .env файл в папке backend:**
   ```bash
   # backend/.env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/signpush
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your_secret_key
   ```

3. **Убедитесь, что PostgreSQL и Redis запущены на localhost**, затем запустите backend:
   ```bash
   python main.py
   # Backend будет доступен на http://localhost:8000
   # API документация на http://localhost:8000/docs
   ```

### Frontend Setup

1. **Установите зависимости Node.js:**
   ```bash
   npm install
   ```

2. **Запустите development сервер:**
   ```bash
   npm start
   # Frontend будет доступен на http://localhost:3000
   ```

3. **Для production сборки:**
   ```bash
   npm run build
   ```

---

## Структура компонентов

### Pages (Страницы)
- **Home** — Главная страница приложения (редирект на My Documents)
- **MyDocuments** — Список всех документов пользователя с фильтрацией и поиском
- **Upload** — Загрузка новых PDF документов с валидацией размера и типа
- **SendDocument** — Отправка документов другим пользователям по email
- **SignatureVerification** — Проверка УНЭП подписи (локальный PDF или документ из БД + `.sig`)
- **Profile** — Просмотр и редактирование информации профиля пользователя
- **Settings** — Страница настроек приложения (расширяемая)
- **Login** — Страница входа в систему
- **Registration** — Страница регистрации новых пользователей
- **Layout** — Главный layout с Header, Sidebar и контентом

### Components (Компоненты)
- **Header** — Заголовок приложения с логотипом, начинается с боковой панели
- **Sidebar** — Боковая панель навигации с функцией сворачивания/разворачивания на десктопе
  - На десктопе (769px+): фиксированная панель слева, свертывается до 80px с tooltip иконками
  - На мобильных (≤768px): выпадающее меню (burger-menu)
  - Содержит: меню навигации, информацию пользователя, кнопку выхода
- **PDFReader** — Просмотр и навигация по страницам PDF
- **PDFDocuments** — Таблица документов с фильтрацией, сортировкой и действиями
- **SignatureModal** — Модальное окно для создания рукописной подписи
- **Paginator** — Компонент пагинации для списков и таблиц
- **DetectOS** — Детектирование операционной системы пользователя
- **RequireAuth** — HOC для защиты маршрутов, требующих аутентификации

### Context (Управление состоянием)
- **AuthProvider** — Контекст для управления состоянием аутентификации (пользователь, токен)
- **SidebarProvider** — Контекст для управления состоянием боковой панели (collapsed/expanded)

---

## Криптография УНЭП

- Подпись формируется в формате CMS/PKCS#7 (`.sig`) на базе ГОСТ Р 34.10/34.11.
- В `signedAttrs` добавляются `content_type`, `message_digest`, `signing_time` и встроенный публичный ключ подписанта.
- Проверка подписи выполняется по встроенному ключу из `signedAttrs`, поэтому валидность подписи не зависит от аккаунта, под которым выполняется проверка.

### Основные API endpoints (УНЭП)

#### Внутренние endpoints (через авторизацию пользователя)

- `POST /api/document/sign/unep/` — Подписание документа в формате УНЭП
- `POST /api/document/verify/unep/` — Проверка валидности УНЭП подписи

#### Endpoints для внешних сервисов (без сессионного токена)

- `POST /api/v1/user/register` — Регистрация пользователя из внешней системы
- `POST /api/v1/document/sign/unep` — Передача документа на подпись УНЭП
- `POST /api/v1/document/sign/img` — Передача документа на графическую подпись
- `POST /api/v1/document/webhook` — Запуск callback отправки подписанного документа
- `POST /api/v1/document/verify/unep` — Проверка УНЭП подписи (по `document_id` или по переданному `document`)

Подробные форматы запросов/ответов и примеры cURL:
- `docs/THIRD_PARTY_CALLBACK_API.md`

---

## 📌 Troubleshooting

### Docker Compose проблемы

**Ошибка: "Port already in use"**
```bash
# Измените порты в docker-compose.yml или используйте другой порт
docker-compose down
# Отредактируйте ports в docker-compose.yml
docker-compose up -d
```

**Ошибка подключения к PostgreSQL**
```bash
# Проверьте, что db контейнер здоров
docker-compose ps
# Посмотрите логи
docker-compose logs db
```

**Redis connection refused**
```bash
# Убедитесь, что Redis контейнер запущен
docker-compose logs redis
docker-compose restart redis
```

### Локальная разработка

**Ошибка импорта модулей Python**
```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows
```

**PostgreSQL не запущен локально**
```bash
# Для Windows (установка с chocolatey):
choco install postgresql

# Для macOS:
brew install postgresql@15
brew services start postgresql@15

# Проверита подключение:
psql -U postgres -d postgres
```

---

**Последнее обновление:** 2026
