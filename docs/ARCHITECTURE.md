# 🏗️ Архитектура проекта SignPush

## Содержание
1. [Архитектурные паттерны](#архитектурные-паттерны)
2. [Схема компонентов](#схема-компонентов)
3. [Потоки данных](#потоки-данных)
4. [Структура проекта](#структура-проекта)

---

## Архитектурные паттерны

### 1. Component-Based Architecture

Приложение построено на основе **компонентной архитектуры React** с четким разделением ответственности.

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│    (UI Components - components/)        │
│  Header, Paginator, SignatureModal      │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│         Container Layer                 │
│      (Pages - pages/)                   │
│  Home, Documents, Login, Layout         │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      State Management Layer             │
│   (Context + Local State)               │
│   AuthContext + useState/useEffect      │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│          Data Layer                     │
│         (API + Storage)                 │
│   Axios → REST API + Cookies            │
└─────────────────────────────────────────┘
```

### 2. Container/Presentational Pattern

**Разделение компонентов на два типа:**

#### Контейнеры (pages/)
- ✅ Управление состоянием
- ✅ Бизнес-логика
- ✅ API запросы
- ✅ Обработка событий

**Примеры:**
- `pages/login/index.js` — логика аутентификации
- `pages/documents/index.js` — загрузка данных с API

#### Презентационные компоненты (components/)
- ✅ Отображение UI
- ✅ Получение данных через props
- ✅ Переиспользование
- ✅ Не зависят от бизнес-логики

**Примеры:**
- `components/header/header.js` — навигация
- `components/paginator/paginator.js` — пагинация

### 3. Context API для глобального состояния

```javascript
// Провайдер
AuthProvider → createContext → AuthContext

// Потребители
useAuth() hook → useContext(AuthContext) → {auth, setAuth}

// Использование
const {auth, setAuth} = useAuth();
```

**Почему Context API:**
- ✅ Встроенный в React (нет внешних зависимостей)
- ✅ Простота для одного глобального состояния
- ✅ Избегание prop drilling
- ✅ Достаточно для небольшого приложения

**Недостатки:**
- ⚠️ Нет персистентности (теряется при refresh)
- ⚠️ Все подписчики перерендериваются при изменении
- ⚠️ Нет DevTools для отладки

### 4. Protected Routes Pattern

```javascript
<Route element={<RequireAuth />}>  {/* HOC Guard */}
    <Route element={<Layout />}>   {/* Shared Layout */}
        <Route index element={<Home />} />
        <Route path="/documents" element={<Documents />} />
    </Route>
</Route>
```

**Логика:**
1. `RequireAuth` проверяет cookies
2. Если авторизован → `<Outlet />` (рендер вложенных роутов)
3. Если нет → `<Navigate to="/login" />`

### 5. Custom Hooks Pattern

```javascript
// hooks/useAuth.js
const useAuth = () => {
    return useContext(AuthContext);
}

// Использование в любом компоненте
const {auth, setAuth} = useAuth();
```

**Преимущества:**
- ✅ Инкапсуляция логики
- ✅ Переиспользование
- ✅ Чистый код компонентов

---

## Схема компонентов

### Дерево компонентов

```
index.js (ReactDOM.render)
│
└── <AuthProvider>
    │
    └── <App> (BrowserRouter)
        │
        ├── <Route path="/login">
        │   └── <Login>
        │       ├── <form>
        │       └── detectOS()
        │
        └── <Route element={<RequireAuth>}>
            │
            └── <Route element={<Layout>}>
                │
                ├── <Header>
                │   ├── <Navbar>
                │   ├── <Link to="/">
                │   ├── <Link to="/documents">
                │   └── <button onClick={logout}>
                │
                └── <Outlet>  {/* Вложенные роуты */}
                    │
                    ├── <Route index>  {/* Home */}
                    │   └── <PdfDocuments>
                    │       ├── <input type="file">
                    │       ├── <Table>
                    │       └── <PdfReader>
                    │           ├── <canvas>
                    │           ├── <Paginator>
                    │           └── <SignatureModal>
                    │               └── <SignatureCanvas>
                    │
                    └── <Route path="/documents">
                        └── <Documents>
                            ├── <Paginator>
                            ├── <Dropdown>
                            ├── <Table>
                            └── <PdfReader>
```

### Взаимодействие компонентов

```
┌──────────────┐
│   Header     │ ← useAuth(), useCookies()
└──────────────┘

┌──────────────┐
│ PdfDocuments │
└──────┬───────┘
       │ state: fileList
       │ props: file (Base64)
       ▼
┌──────────────┐
│  PdfReader   │
└──────┬───────┘
       │ callback: handleCallback
       ▼
┌──────────────┐
│SignatureModal│
└──────────────┘
```

---

## Потоки данных

### 1. Поток аутентификации

```
┌─────────────────────────────────────────────────────┐
│ 1. User Input (Login Form)                          │
│    email: "user@example.com"                        │
│    password: "password123"                          │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. API Request                                      │
│    PATCH /user/s/auth/password                      │
│    Body: {email, password: ['p','a','s','s'...]}   │
│    Headers: {apiKey, Content-Type}                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. API Response                                     │
│    {status: 0, token: "abc123...", message: "OK"}  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 4. Cookie Storage                                   │
│    setCookie('user', email, {expires: ...})         │
│    setCookie('token', token, {expires: ...})        │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 5. Update Context                                   │
│    setAuth({user: email})                           │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 6. Navigation                                       │
│    navigate(from || '/', {replace: true})           │
└─────────────────────────────────────────────────────┘
```

### 2. Поток загрузки документа

```
┌─────────────────────────────────────────────────────┐
│ 1. File Selection                                   │
│    <input type="file" accept="application/pdf">     │
│    User selects: document.pdf (150KB)              │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. FileReader API                                   │
│    const reader = new FileReader();                 │
│    reader.readAsDataURL(file);                      │
│    → "data:application/pdf;base64,JVBERi0xLjQK..."  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. Extract Base64                                   │
│    base64String = base64                            │
│        .replace('data:', '')                        │
│        .replace(/^.+,/, '')                         │
│    → "JVBERi0xLjQK..."                              │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 4. Calculate SHA-256 Hash                           │
│    const shaObj = new jsSHA("SHA-256", "B64");      │
│    shaObj.update(base64String);                     │
│    const hash = shaObj.getHash("B64");              │
│    → "7B8E9A2F..."                                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 5. Add Metadata                                     │
│    file.hash = hash;                                │
│    file.created_at = DateTime.fromMillis(...);      │
│    file.base64 = base64;                            │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 6. Update State                                     │
│    setFileList(existing => [...existing, file]);    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 7. Render Table                                     │
│    <Table> with file list                           │
└─────────────────────────────────────────────────────┘
```

### 3. Поток рендеринга PDF

```
┌─────────────────────────────────────────────────────┐
│ 1. Base64 PDF Data                                  │
│    file = "data:application/pdf;base64,..."         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. Dynamic Import PDF.js                            │
│    const pdfJS = await import('pdfjs-dist/...');    │
│    pdfJS.GlobalWorkerOptions.workerSrc = '...';     │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. Load PDF Document (Web Worker)                   │
│    let pdf = await pdfJS.getDocument(file).promise; │
│    → PDF Object {numPages: 5, ...}                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 4. Get Page                                         │
│    const page = await pdf.getPage(pageNumber);      │
│    → Page Object                                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 5. Calculate Viewport                               │
│    const viewport = page.getViewport({scale: 2.5}); │
│    → {width: 1275, height: 1650, ...}               │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 6. Setup Canvas                                     │
│    canvas.width = viewport.width;                   │
│    canvas.height = viewport.height;                 │
│    const ctx = canvas.getContext('2d');             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 7. Render to Canvas                                 │
│    page.render({canvasContext: ctx, viewport});     │
│    → Rendered PDF page on canvas                    │
└─────────────────────────────────────────────────────┘
```

### 4. Поток создания подписи

```
┌─────────────────────────────────────────────────────┐
│ 1. User Selects Area (Mouse Events)                 │
│    mousedown → save startX, startY                  │
│    mousemove → draw rectangle                       │
│    mouseup → save width, height                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. Open SignatureModal                              │
│    setShow(true)                                    │
│    → Modal with fullscreen canvas                   │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. User Draws Signature                             │
│    <SignatureCanvas ref={canvasRef} />              │
│    → User draws with mouse/touch                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 4. Export Signature                                 │
│    const signatureData = canvasRef.toDataURL();     │
│    → "data:image/png;base64,iVBORw0KGgo..."         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 5. Callback to Parent                               │
│    handleCallback(signatureData);                   │
│    setShow(false);                                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 6. Load Signature Image                             │
│    const img = new Image();                         │
│    img.src = signatureData;                         │
│    img.onload = () => {...}                         │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 7. Draw on PDF Canvas                               │
│    ctx.drawImage(img, squareX, squareY,             │
│                  squareWidth, squareHeight);        │
│    → Signature placed on document                   │
└─────────────────────────────────────────────────────┘
```

---

## Структура проекта

### Файловая организация

```
signpush-main/
│
├── public/                              
│   ├── index.html                       # HTML шаблон
│   ├── logo.png                         # Логотип (темный)
│   ├── logo_white.png                   # Логотип (светлый)
│   ├── pdf.worker.js                    # Web Worker для PDF.js (1.9MB)
│   ├── pdfjs-3.10.111-dist/             # PDF.js библиотека
│   ├── pdfjs-3.11.174-dist/             # Дублирующая версия (не используется)
│   ├── HarmoniaSansProCyr-B.woff        # Кастомный шрифт (жирный)
│   ├── HarmoniaSansProCyr-L.woff        # Кастомный шрифт (легкий)
│   ├── test.pdf                         # Тестовый PDF
│   ├── favicon.ico                      # Иконка сайта
│   ├── manifest.json                    # PWA манифест
│   └── robots.txt                       # SEO
│
├── src/
│   │
│   ├── api/
│   │   └── axios.js                     # Конфигурация Axios инстанса
│   │
│   ├── components/                      # Переиспользуемые компоненты
│   │   │
│   │   ├── detect-os/
│   │   │   └── detect-os.js             # Определение ОС клиента
│   │   │
│   │   ├── header/
│   │   │   ├── header.js                # Шапка с навигацией
│   │   │   └── header.css               # Стили шапки
│   │   │
│   │   ├── paginator/
│   │   │   └── paginator.js             # Wrapper для react-paginate
│   │   │
│   │   ├── pdf-documents/
│   │   │   ├── pdf-documents.js         # Загрузка и таблица файлов
│   │   │   └── pdf-documents.css        # Стили таблицы
│   │   │
│   │   ├── pdf-reader/
│   │   │   ├── pdf-reader.js            # Просмотр и подписание PDF
│   │   │   └── pdf-reader.css           # Стили viewer
│   │   │
│   │   ├── require-auth/
│   │   │   └── index.js                 # HOC для защиты роутов
│   │   │
│   │   └── signature-modal/
│   │       ├── signature-modal.js       # Модальное окно подписи
│   │       └── signature-modal.css      # Стили модалки
│   │
│   ├── context/
│   │   └── AuthProvider.js              # React Context для auth
│   │
│   ├── hooks/
│   │   └── useAuth.js                   # Hook для доступа к AuthContext
│   │
│   ├── pages/                           # Страницы-контейнеры
│   │   │
│   │   ├── documents/
│   │   │   ├── index.js                 # Список документов с API
│   │   │   └── documents.css            # Стили страницы
│   │   │
│   │   ├── home/
│   │   │   ├── index.js                 # Главная страница
│   │   │   └── home.css                 # Стили (пустой)
│   │   │
│   │   ├── layout/
│   │   │   └── index.js                 # Layout wrapper (Header + Outlet)
│   │   │
│   │   └── login/
│   │       ├── index.js                 # Форма аутентификации
│   │       ├── main.css                 # Основные стили
│   │       └── site.css                 # Дополнительные стили
│   │
│   ├── fonts/                           # Директория для шрифтов (пустая)
│   │
│   ├── App.js                           # Корневой компонент + роутинг
│   ├── index.js                         # Entry point
│   └── index.css                        # Глобальные стили
│
├── docs/                                # Документация
├── node_modules/                        # Зависимости (718MB)
├── package.json                         # Конфигурация проекта
├── package-lock.json                    # Lock file
├── .gitignore                           # Git исключения
└── README.md                            # Основная документация
```

### Принципы организации

#### 1. **Feature-based structure**
Каждый компонент в своей директории:
```
component-name/
├── component-name.js     # Логика
└── component-name.css    # Стили
```

#### 2. **Separation of Concerns**
- `pages/` — бизнес-логика, API, state
- `components/` — UI, props, переиспользование
- `api/` — конфигурация HTTP
- `context/` — глобальное состояние
- `hooks/` — переиспользуемая логика

#### 3. **Colocation**
Связанные файлы рядом друг с другом

### Метрики

| Метрика | Значение |
|---------|----------|
| Всего файлов | ~1100 (с node_modules) |
| Строк кода (src/) | ~900 |
| Компонентов | 11 |
| Страниц | 4 |
| Маршрутов | 3 |
| Зависимостей | 25 production + 1 dev |
| Размер public/ | ~4.5MB |
| Размер node_modules/ | ~718MB |

---

## Выводы

### Сильные стороны архитектуры
- ✅ Четкое разделение ответственности
- ✅ Переиспользуемые компоненты
- ✅ Простая и понятная структура
- ✅ Масштабируемая организация файлов

### Слабые стороны
- ⚠️ Отсутствие слоя services для API
- ⚠️ Нет директории utils для вспомогательных функций
- ⚠️ Отсутствует типизация (TypeScript/PropTypes)
- ⚠️ Большой PdfReader компонент (261 строка)

### Рекомендации
1. Добавить директорию `services/` для API логики
2. Создать `utils/` для helper функций
3. Разбить PdfReader на подкомпоненты
4. Добавить PropTypes или TypeScript
5. Создать `constants/` для конфигурации
