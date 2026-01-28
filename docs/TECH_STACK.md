# 💻 Технологический стек SignPush

## Содержание
1. [Обзор зависимостей](#обзор-зависимостей)
2. [Детальное обоснование выбора](#детальное-обоснование-выбора)
3. [Сравнение с альтернативами](#сравнение-с-альтернативами)
4. [Конфигурация сборки](#конфигурация-сборки)

---

## Обзор зависимостей

### Core Framework (React Ecosystem)

| Библиотека | Версия | Размер | Назначение |
|------------|--------|--------|------------|
| **react** | 18.2.0 | 44KB | UI библиотека, компонентный подход |
| **react-dom** | 18.2.0 | 130KB | Рендеринг React в DOM |
| **react-router-dom** | 6.16.0 | 10KB | Клиентская маршрутизация |
| **react-scripts** | 5.0.1 | - | CRA build system (dev) |

### HTTP & State Management

| Библиотека | Версия | Размер | Назначение |
|------------|--------|--------|------------|
| **axios** | 1.5.1 | 13KB | HTTP клиент |
| **js-cookie** | 3.0.5 | 1.4KB | Управление cookies |
| **react-cookie** | 6.1.1 | 3KB | React hooks для cookies |

### UI Framework & Components

| Библиотека | Версия | Размер | Назначение |
|------------|--------|--------|------------|
| **bootstrap** | 5.3.2 | 200KB | CSS фреймворк |
| **react-bootstrap** | 2.9.0 | 90KB | Bootstrap компоненты для React |
| **bootstrap-icons** | 1.11.1 | 150KB | Иконки |
| **react-overlays** | 5.2.1 | 8KB | Overlay примитивы |
| **react-paginate** | 8.2.0 | 15KB | Компонент пагинации |

### PDF Processing

| Библиотека | Версия | Размер | Назначение |
|------------|--------|--------|------------|
| **pdfjs-dist** | 3.10.111 | 2MB | PDF рендеринг |
| **react-pdf** | 7.3.3 | 25KB | React wrapper для PDF.js |

### Utilities

| Библиотека | Версия | Размер | Назначение |
|------------|--------|--------|------------|
| **jssha** | 3.3.1 | 15KB | SHA-256 хеширование |
| **luxon** | 3.4.3 | 70KB | Работа с датами |
| **react-signature-canvas** | 1.0.6 | 12KB | Рукописная подпись |

### Testing (встроено в CRA)

| Инструмент | Версия | Назначение |
|------------|--------|------------|
| **@testing-library/react** | 13.4.0 | Тестирование компонентов |
| **@testing-library/jest-dom** | 5.17.0 | Jest матчеры для DOM |
| **@testing-library/user-event** | 13.5.0 | Симуляция событий |
| **web-vitals** | 2.1.4 | Метрики производительности |

---

## Детальное обоснование выбора

### 1. React 18.2.0

#### Почему выбран React?

**Преимущества:**
- ✅ **Virtual DOM** — оптимизация рендеринга
- ✅ **Компонентный подход** — переиспользование кода
- ✅ **Hooks** — функциональные компоненты с состоянием
- ✅ **Богатая экосистема** — тысячи библиотек
- ✅ **Большое сообщество** — решения типичных проблем
- ✅ **Стабильность** — проверен на production

**React 18 фичи:**
```javascript
// Автоматический batching
setState1(value1);
setState2(value2);
// → Один re-render вместо двух

// Concurrent rendering (в будущем)
<Suspense fallback={<Loading />}>
    <Component />
</Suspense>
```

**Альтернативы:**
- **Vue.js** — проще в изучении, template syntax
- **Angular** — full-featured framework, TypeScript
- **Svelte** — compile-time framework, меньше кода

**Вывод:** React оптимален для проекта такого размера.

---

### 2. React Router DOM 6.16.0

#### Почему React Router?

**Преимущества:**
- ✅ **Declarative routing** — роуты как компоненты
- ✅ **Вложенные роуты** — Layout pattern
- ✅ **Data loading** — loader функции (не используется)
- ✅ **Защищенные роуты** — через HOC
- ✅ **History API** — браузерная навигация

**Использование в проекте:**
```javascript
<BrowserRouter>
  <Routes>
    <Route element={<RequireAuth />}>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
      </Route>
    </Route>
  </Routes>
</BrowserRouter>
```

**v6 vs v5:**
```javascript
// v5 (старый)
<Route path="/user/:id" component={User} />

// v6 (новый)
<Route path="/user/:id" element={<User />} />
```

**Альтернативы:**
- **React Location** — новая библиотека, async routing
- **Reach Router** — deprecated, слит с React Router
- **Wouter** — минималистичный, 1.5KB

**Вывод:** React Router v6 — стандарт индустрии.

---

### 3. Axios 1.5.1

#### Почему Axios вместо Fetch?

**Сравнение:**

```javascript
// ❌ Fetch API
fetch(url)
  .then(response => {
    if (!response.ok) throw new Error('HTTP error');
    return response.json();
  })
  .then(data => console.log(data))
  .catch(error => console.error(error));

// ✅ Axios
axios.get(url)
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

**Преимущества Axios:**

| Функция | Axios | Fetch |
|---------|-------|-------|
| Авто JSON parse | ✅ | ❌ |
| Timeout | ✅ | ❌ |
| Interceptors | ✅ | ❌ |
| Cancel requests | ✅ | ✅ (AbortController) |
| Progress events | ✅ | ❌ |
| Old browser support | ✅ | ❌ (polyfill) |

**Interceptors пример:**
```javascript
axios.interceptors.request.use(config => {
  config.headers.token = Cookies.get('token');
  return config;
});

axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login
    }
    return Promise.reject(error);
  }
);
```

**Проблема в проекте:**
```javascript
// src/api/axios.js
export default axios.create({
    baseUrl: 'https://test.signpush.ru/api/v4.1'  // ❌ Опечатка!
});
```

Должно быть `baseURL` (с заглавными буквами). Из-за этого базовый URL не применяется!

**Вывод:** Axios правильный выбор, но требует исправления конфигурации.

---

### 4. Bootstrap 5.3.2 + React-Bootstrap 2.9.0

#### Почему Bootstrap?

**Преимущества:**
- ✅ **Быстрая разработка** — готовые компоненты
- ✅ **Responsive grid** — адаптивность из коробки
- ✅ **Кроссбраузерность** — поддержка старых браузеров
- ✅ **Документация** — подробная и понятная
- ✅ **Кастомизация** — через SASS переменные

**Использование в проекте:**
```javascript
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import Dropdown from 'react-bootstrap/Dropdown';
```

**Почему React-Bootstrap, а не Bootstrap напрямую:**
- ✅ Управляемые компоненты (controlled components)
- ✅ Нет зависимости от jQuery
- ✅ React-friendly API
- ✅ TypeScript типы

**Недостатки Bootstrap:**
- ⚠️ Большой размер bundle (~200KB CSS)
- ⚠️ Стандартный дизайн (выглядит как Bootstrap)
- ⚠️ Ограниченная кастомизация без SASS

**Альтернативы:**

| Фреймворк | Размер | Особенности |
|-----------|--------|-------------|
| **Material-UI** | 300KB | Material Design, больше компонентов |
| **Ant Design** | 500KB | Enterprise UI, китайский стиль |
| **Chakra UI** | 150KB | Accessibility, темизация |
| **Tailwind CSS** | ~50KB | Utility-first, полная кастомизация |

**Вывод:** Bootstrap подходит для быстрого прототипирования.

---

### 5. PDF.js (pdfjs-dist 3.10.111)

#### Почему PDF.js?

**Преимущества:**
- ✅ **Mozilla проект** — надежность и поддержка
- ✅ **Web Workers** — парсинг в отдельном потоке
- ✅ **Canvas rendering** — высокое качество
- ✅ **Полная поддержка PDF** — формы, аннотации, шифрование
- ✅ **Без серверной обработки** — всё в браузере

**Архитектура PDF.js:**
```
Main Thread (UI)
    ↓
postMessage()
    ↓
Web Worker Thread (pdf.worker.js)
    ↓ (парсинг PDF)
postMessage(parsed data)
    ↓
Main Thread
    ↓ (рендеринг)
Canvas 2D Context
```

**Использование:**
```javascript
// Динамический import для code splitting
const pdfJS = await import('pdfjs-dist/build/pdf');

// Настройка Worker
pdfJS.GlobalWorkerOptions.workerSrc = '/pdf.worker.js';

// Загрузка документа
const pdf = await pdfJS.getDocument(fileBase64).promise;

// Рендеринг страницы
const page = await pdf.getPage(1);
const viewport = page.getViewport({ scale: 2.5 });
page.render({ canvasContext, viewport });
```

**Почему динамический import:**
```javascript
// ❌ Статический import
import * as pdfJS from 'pdfjs-dist/build/pdf';
// → PDF.js (~2MB) загружается сразу

// ✅ Динамический import
const pdfJS = await import('pdfjs-dist/build/pdf');
// → PDF.js загружается только при необходимости
```

**Альтернативы:**
- **react-pdf** — wrapper, но используется вместе с pdfjs-dist
- **pdf-lib** — для создания/редактирования PDF
- **jsPDF** — генерация PDF из HTML/Canvas

**Вывод:** PDF.js — единственный полноценный рендерер PDF в браузере.

---

### 6. jsSHA 3.3.1

#### Почему jsSHA?

**Преимущества:**
- ✅ **Поддержка форматов** — Base64, HEX, Text, ArrayBuffer
- ✅ **Алгоритмы** — SHA-1, SHA-256, SHA-512, SHA3, HMAC
- ✅ **Легковесность** — ~15KB gzipped
- ✅ **Кроссбраузерность** — работает везде
- ✅ **Синхронный API** — не требует async/await

**Использование:**
```javascript
const shaObj = new jsSHA("SHA-256", "B64");
shaObj.update(base64String);
const hash = shaObj.getHash("B64");
// → "7B8E9A2F3C1D4E5F6A7B8C9D0E1F2A3B..."
```

**Сравнение с Web Crypto API:**

```javascript
// ❌ SubtleCrypto (сложнее)
const encoder = new TextEncoder();
const data = encoder.encode(text);
const hashBuffer = await crypto.subtle.digest('SHA-256', data);
const hashArray = Array.from(new Uint8Array(hashBuffer));
const hash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

// ✅ jsSHA (проще)
const shaObj = new jsSHA("SHA-256", "TEXT");
shaObj.update(text);
const hash = shaObj.getHash("HEX");
```

**Почему не SubtleCrypto:**
- ❌ Асинхронный API
- ❌ Работает только в secure context (HTTPS/localhost)
- ❌ Нет поддержки в IE11
- ❌ Сложная работа с Base64
- ❌ Только ArrayBuffer input

**Вывод:** jsSHA оптимален для хеширования Base64 данных.

---

### 7. Luxon 3.4.3

#### Почему Luxon?

**Сравнение библиотек дат:**

| Библиотека | Размер | Immutable | Timezone | i18n |
|------------|--------|-----------|----------|------|
| **Moment.js** | 230KB | ❌ | Plugin | ✅ |
| **date-fns** | 30KB | ✅ | Plugin | ✅ |
| **Day.js** | 7KB | ✅ | Plugin | Plugin |
| **Luxon** | 70KB | ✅ | ✅ | ✅ |

**Преимущества Luxon:**
- ✅ **Immutable** — безопасная работа
- ✅ **Intl API** — использует стандартный API браузера
- ✅ **Timezone** — встроенная поддержка
- ✅ **Читаемый API** — chainable методы
- ✅ **Форматирование** — гибкие опции

**Использование в проекте:**
```javascript
// UNIX timestamp → читаемая дата
DateTime.fromSeconds(1704096000).toFormat('ff');
// → "1 января 2024 г., 12:00"

// Миллисекунды → дата
DateTime.fromMillis(file.lastModified).toFormat('ff');
```

**Форматы:**
```javascript
DateTime.now().toFormat('ff');     // "1 января 2024 г., 12:00"
DateTime.now().toFormat('yyyy-MM-dd');  // "2024-01-01"
DateTime.now().toISO();            // "2024-01-01T12:00:00.000+03:00"
```

**Альтернативы:**
- **date-fns** — модульный, tree-shakeable
- **Day.js** — минималистичный, совместим с Moment.js API

**Вывод:** Luxon — modern choice с хорошим балансом функций и размера.

---

### 8. react-signature-canvas 1.0.6

#### Почему react-signature-canvas?

**Преимущества:**
- ✅ **React wrapper** — интеграция с lifecycle
- ✅ **Touch support** — мобильные устройства
- ✅ **Smooth curves** — Bezier сглаживание
- ✅ **Export** — PNG, JPG, SVG
- ✅ **Легковесность** — wrapper над Signature Pad

**Использование:**
```javascript
import SignatureCanvas from 'react-signature-canvas';

function SignatureModal() {
  let canvasRef = useRef(null);
  
  return (
    <SignatureCanvas 
      ref={(ref) => { canvasRef = ref }}
      canvasProps={{ className: 'sigPad' }}
    />
  );
  
  // Экспорт
  const signature = canvasRef.toDataURL('image/png');
}
```

**API:**
```javascript
canvasRef.clear();                    // Очистка
canvasRef.toDataURL('image/png');     // Экспорт в Base64
canvasRef.fromDataURL(dataURL);       // Загрузка подписи
canvasRef.isEmpty();                  // Проверка пустоты
```

**Альтернативы:**
- **react-canvas-draw** — больше функций (undo, цвета)
- **Signature Pad** — нативная библиотека без React wrapper

**Вывод:** Оптимальный выбор для простой подписи.

---

### 9. react-paginate 8.2.0

#### Почему react-paginate?

**Преимущества:**
- ✅ **Готовое решение** — не нужно писать логику
- ✅ **Accessibility** — ARIA labels
- ✅ **Кастомизация** — Bootstrap/Material-UI стили
- ✅ **Гибкость** — много опций конфигурации

**Использование:**
```javascript
<ReactPaginate
  pageCount={Math.ceil(items.length / itemsPerPage)}
  onPageChange={handlePageClick}
  previousLabel="Предыдущая"
  nextLabel="Следующая"
  pageClassName="page-item"
  pageLinkClassName="page-link"
  previousClassName="page-item"
  previousLinkClassName="page-link"
  nextClassName="page-item"
  nextLinkClassName="page-link"
  containerClassName="pagination"
  activeClassName="active"
  marginPagesDisplayed={1}
  pageRangeDisplayed={1}
/>
```

**Альтернативы:**
- **rc-pagination** — более гибкий
- **Custom implementation** — полный контроль

**Вывод:** Простое и надежное решение.

---

## Сравнение с альтернативами

### State Management: Context API vs Redux

**Context API (текущий выбор):**
```javascript
// ✅ Простота
const {auth, setAuth} = useAuth();

// ❌ Производительность
// Все подписчики ре-рендерятся при изменении
```

**Redux:**
```javascript
// ✅ DevTools, middleware, performance
const auth = useSelector(state => state.auth);
const dispatch = useDispatch();

// ❌ Boilerplate
// Много кода для простых операций
```

**Вывод:** Для данного проекта Context API достаточен.

---

### Styling: Bootstrap vs Tailwind CSS

**Bootstrap (текущий выбор):**
```jsx
<Button variant="primary">Кнопка</Button>
```
- ✅ Быстрая разработка
- ❌ Большой bundle size

**Tailwind CSS:**
```jsx
<button className="bg-blue-500 hover:bg-blue-700 text-white px-4 py-2">
  Кнопка
</button>
```
- ✅ Меньший размер (~50KB)
- ❌ Много классов в JSX

**Вывод:** Bootstrap лучше для быстрого прототипирования.

---

## Конфигурация сборки

### package.json Scripts

```json
{
  "scripts": {
    "start": "react-scripts --max_old_space_size=512 start",
    "build": "react-scripts --max_old_space_size=512 build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
```

### Почему --max_old_space_size=512?

**Назначение:** Ограничение памяти Node.js до 512MB.

**Причины использования:**
- ✅ Предотвращение утечек памяти
- ✅ Оптимизация для слабых машин
- ✅ Контроль использования ресурсов

**Проблемы:**
- ⚠️ Может быть недостаточно для больших проектов
- ⚠️ Default в Node.js ~1.7GB на 64-bit

**Рекомендация:** Увеличить до 2048 или убрать.

---

### Create React App (CRA)

**Что включает react-scripts:**
- **Webpack 5** — модульная сборка
- **Babel** — транспиляция ES6+
- **ESLint** — линтинг кода
- **Jest** — тестирование
- **PostCSS** — обработка CSS
- **webpack-dev-server** — development сервер

**Преимущества CRA:**
- ✅ Zero configuration
- ✅ Hot Module Replacement
- ✅ Production оптимизации
- ✅ Service Worker support

**Недостатки CRA:**
- ❌ Нет доступа к webpack config (без eject)
- ❌ Большой размер зависимостей
- ❌ Медленная сборка больших проектов

**Альтернативы:**
- **Vite** — быстрее, ESM
- **Next.js** — SSR, роутинг
- **Custom Webpack** — полный контроль

---

## Выводы

### Оптимальные выборы
- ✅ React 18 — стабильный и мощный
- ✅ PDF.js — нет альтернатив
- ✅ jsSHA — правильный выбор для Base64
- ✅ Luxon — современный API дат

### Спорные выборы
- ⚠️ Bootstrap — большой размер, можно заменить на Tailwind
- ⚠️ Context API — может не хватить при росте
- ⚠️ Cookies для токенов — лучше localStorage

### Проблемы конфигурации
- ❌ Опечатка в axios.js (`baseUrl` → `baseURL`)
- ❌ Маленький memory limit (512MB)
- ❌ Дублирование PDF.js дистрибутивов

### Рекомендации
1. Исправить конфигурацию Axios
2. Увеличить memory limit
3. Удалить неиспользуемый pdfjs-3.11.174-dist
4. Рассмотреть миграцию на Vite для ускорения сборки
