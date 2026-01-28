# 🧩 Анализ компонентов: UI компоненты

## Содержание
1. [Header — Навигация](#1-header)
2. [PdfDocuments — Загрузка файлов](#2-pdfdocuments)
3. [Paginator — Пагинация](#3-paginator)
4. [SignatureModal — Создание подписи](#4-signaturemodal)
5. [detectOS — Определение ОС](#5-detectos)

---

## 1. Header

**Файл:** `src/components/header/header.js` (44 строки)

### Назначение
Навигационная панель с отображением пользователя и функцией выхода.

### Ключевые проблемы

**🚨 Неполный logout:**
```javascript
const handleLogout = async (e) => {
    removeCookie('user');  // ✅ Удаляет user
    // ❌ НЕ удаляет token!
    setAuth(null);
    navigate('/', { replace: true });  // ❌ Редирект на защищенную страницу
};
```

**Правильная реализация:**
```javascript
const handleLogout = async (e) => {
    e.preventDefault();
    removeCookie('user', { path: '/' });
    removeCookie('token', { path: '/' });  // ✅ Удаляем токен
    setAuth(null);
    navigate('/login', { replace: true });  // ✅ Редирект на login
};
```

### Рекомендации
- ✅ Удалять все cookies при logout
- ✅ Использовать `NavLink` для активных ссылок
- ✅ Добавить dropdown меню пользователя
- ✅ Мобильная адаптация с navbar-toggler

---

## 2. PdfDocuments

**Файл:** `src/components/pdf-documents/pdf-documents.js` (99 строк)

### Назначение
Загрузка PDF файлов с вычислением SHA-256 хеша и конвертацией в Base64.

### Основная логика

**Обработка загрузки:**
```javascript
const handleFileChange = async ({currentTarget: {files}}) => {
    // 1. Конвертация в Base64
    const base64 = await getBase64(files[0]);
    
    // 2. Вычисление SHA-256
    const base64String = base64.replace(/^data:.+,/, '');
    const shaObj = new jsSHA("SHA-256", "B64");
    shaObj.update(base64String);
    files[0]['hash'] = shaObj.getHash("B64");
    
    // 3. Добавление метаданных
    files[0]['created_at'] = DateTime.fromMillis(files[0].lastModified).toFormat('ff');
    files[0]['base64'] = base64;
};
```

### Проблемы

**❌ Мутация объекта File:**
```javascript
files[0]['hash'] = shaObj.getHash("B64");  // Прямая мутация
```

**✅ Лучше:**
```javascript
const enrichedFile = {
    file: files[0],
    name: files[0].name,
    hash: shaObj.getHash("B64"),
    created_at: DateTime.fromMillis(files[0].lastModified).toFormat('ff'),
    base64: base64
};
```

**❌ Нет валидации:**
```javascript
// Добавить проверку типа и размера
if (file.type !== 'application/pdf') {
    alert('Пожалуйста, выберите PDF файл');
    return;
}

if (file.size > 10 * 1024 * 1024) {  // 10MB
    alert('Файл слишком большой');
    return;
}
```

### Input Reset Trick
```javascript
const [inputKey, setInputKey] = useState(0);

<input key={inputKey} type="file" onChange={handleFileChange} />

// После загрузки
setInputKey(key => key + 1);  // React пересоздает input
```

**Зачем:** HTML input не позволяет загрузить тот же файл дважды подряд.

### Рекомендации
- ✅ Добавить валидацию типа и размера файла
- ✅ Обработка ошибок с try/catch
- ✅ Loading state во время обработки
- ✅ Вынести утилиты в `utils/fileUtils.js`

---

## 3. Paginator

**Файл:** `src/components/paginator/paginator.js` (32 строки)

### Назначение
Wrapper над `react-paginate` с Bootstrap стилями.

### Конфигурация
```javascript
<ReactPaginate
    pageCount={Math.ceil(items.length / itemsPerPage)}
    pageRangeDisplayed={1}      // Страниц слева/справа
    marginPagesDisplayed={1}    // Страниц на краях
    forcePage={currentPage}     // Controlled component
    // Bootstrap классы
    containerClassName='pagination'
    pageClassName='page-item'
    pageLinkClassName='page-link'
    activeClassName='active'
/>
```

**Визуализация:**
```
< Предыдущая | 1 | ... | 5 | 6 | 7 | ... | 20 | Следующая >
```

### Проблемы

**❌ Передача всего массива:**
```javascript
const pageCount = Math.ceil(items.length / itemsPerPage);
// В Documents.js передается Array(25) для подсчета
```

**✅ Лучше передавать только число:**
```javascript
<Paginator 
    totalItems={1000}  // Только число
    itemsPerPage={10}
    currentPage={currentPage}
    onPageChange={handlePageClick}
/>
```

### Рекомендации
- ✅ Передавать `totalItems` вместо `items`
- ✅ Скрывать при 0 или 1 странице
- ✅ Добавить ARIA labels для accessibility

---

## 4. SignatureModal

**Файл:** `src/components/signature-modal/signature-modal.js` (46 строк)

### Назначение
Модальное окно для создания рукописной подписи с использованием `react-signature-canvas`.

### API SignatureCanvas
```javascript
canvasRef.toDataURL()           // Экспорт в Base64 PNG
canvasRef.toDataURL('image/jpeg', 0.5)  // JPEG с качеством
canvasRef.clear()               // Очистка
canvasRef.isEmpty()             // Проверка пустоты
canvasRef.fromDataURL(dataURL)  // Загрузка подписи
```

### Проблемы

**❌ Нет кнопки очистки:**
```javascript
const handleClear = () => {
    canvasRef.clear();
};

<Button variant="warning" onClick={handleClear}>
    <i className="bi bi-eraser"></i> Очистить
</Button>
```

**❌ Нет проверки пустой подписи:**
```javascript
const handleAdd = async () => {
    if (canvasRef.isEmpty()) {
        alert('Пожалуйста, нарисуйте подпись');
        return;
    }
    handleCallback(canvasRef.toDataURL());
};
```

**❌ Нет настроек кисти:**
```javascript
const [penColor, setPenColor] = useState('black');
const [penWidth, setPenWidth] = useState(2);

<SignatureCanvas 
    penColor={penColor}
    minWidth={penWidth * 0.5}
    maxWidth={penWidth}
    canvasProps={{width: 700, height: 300}}
/>
```

### Рекомендации
- ✅ Добавить кнопку "Очистить"
- ✅ Проверять isEmpty() перед сохранением
- ✅ Настройки цвета и толщины пера
- ✅ Backdrop="static" для предотвращения случайного закрытия

---

## 5. detectOS

**Файл:** `src/components/detect-os/detect-os.js` (25 строк)

### Назначение
Определение операционной системы пользователя для отправки в API.

### Код
```javascript
export default function detectOS() {
    let userAgent = window.navigator.userAgent,
        platform = window.navigator.platform,
        macosPlatforms = ['Macintosh', 'MacIntel', 'MacPPC', 'Mac68K'],
        windowsPlatforms = ['Win32', 'Win64', 'Windows', 'WinCE'],
        iosPlatforms = ['iPhone', 'iPad', 'iPod'],
        os = null;

    if (macosPlatforms.indexOf(platform) !== -1) {
        os = 'Mac OS';
    } else if (iosPlatforms.indexOf(platform) !== -1) {
        os = 'iOS';
    } else if (windowsPlatforms.indexOf(platform) !== -1) {
        os = 'Windows';
    } else if (/Android/.test(userAgent)) {
        os = 'Android';
    } else if (/Linux/.test(platform)) {
        os = 'Linux';
    }

    return os;
}
```

### Использование
```javascript
// В Login.js
const os = detectOS();  // "Windows", "Mac OS", etc.

// Отправка в API
{
    'device': {
        'model': 'Virtual',
        'os': os
    }
}
```

### Проблемы

**⚠️ Deprecated API:**
```javascript
navigator.platform  // Deprecated в современных браузерах
```

**Современная альтернатива:**
```javascript
// User-Agent Client Hints API
navigator.userAgentData?.platform  // "Windows", "macOS", "Linux"
```

**❌ Не утилита, а компонент:**
Находится в `components/`, но это не React компонент.

**✅ Лучше:** Переместить в `utils/detectOS.js`

### Улучшенная версия
```javascript
// utils/detectOS.js
export function detectOS() {
    // Попытка использовать новый API
    if (navigator.userAgentData?.platform) {
        const platform = navigator.userAgentData.platform;
        if (platform === 'Windows') return 'Windows';
        if (platform === 'macOS') return 'Mac OS';
        if (platform === 'Linux') return 'Linux';
    }
    
    // Fallback на старый метод
    const userAgent = navigator.userAgent;
    const platform = navigator.platform;
    
    if (/Mac/.test(platform)) return 'Mac OS';
    if (/iPhone|iPad|iPod/.test(userAgent)) return 'iOS';
    if (/Win/.test(platform)) return 'Windows';
    if (/Android/.test(userAgent)) return 'Android';
    if (/Linux/.test(platform)) return 'Linux';
    
    return 'Unknown';
}
```

### Рекомендации
- ✅ Использовать User-Agent Client Hints API
- ✅ Переместить в `utils/`
- ✅ Добавить fallback для старых браузеров
- ✅ Возвращать 'Unknown' вместо null

---

## Заключение по UI компонентам

### Сильные стороны
- ✅ Переиспользуемые компоненты
- ✅ Bootstrap интеграция
- ✅ SHA-256 хеширование для безопасности
- ✅ Рукописная подпись с canvas

### Критические проблемы
- 🚨 Неполный logout (токен не удаляется)
- 🚨 Мутация объектов File
- 🚨 Отсутствие валидации файлов

### Средние проблемы
- ⚠️ Нет проверки пустой подписи
- ⚠️ Deprecated navigator.platform
- ⚠️ Отсутствие обработки ошибок

### Рекомендации по улучшению

| Компонент | Приоритет | Действие |
|-----------|-----------|----------|
| Header | 🔴 Критический | Исправить logout, удалять token |
| PdfDocuments | 🟠 Высокий | Добавить валидацию, обработку ошибок |
| SignatureModal | 🟡 Средний | Проверка isEmpty(), кнопка Clear |
| Paginator | 🟡 Средний | Передавать totalItems вместо массива |
| detectOS | 🟢 Низкий | Переместить в utils, использовать новый API |

### Следующие шаги
1. Немедленно исправить logout в Header
2. Добавить валидацию файлов в PdfDocuments
3. Улучшить SignatureModal с проверками
4. Оптимизировать Paginator
5. Рефакторинг detectOS в утилиту
