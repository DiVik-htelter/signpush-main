# Автоматическая отправка заголовков token и email

## Описание
Добавлен request intерцептор в axios, который автоматически добавляет `token` и `email` в заголовки поля для всех API запросов. Также устанавливает `Content-Type: application/json` по умолчанию.

## Изменения

### 1. `src/api/axios.js` - Request Interceptor
Добавлен интерцептор для всех исходящих запросов:

```javascript
instance.interceptors.request.use(
    (config) => {
        // Добавляем token в заголовок, если существует
        if (Cookies.get('token')) {
            config.headers['token'] = Cookies.get('token');
        } else {
            config.headers['token'] = -1;
        }
        
        // Добавляем email в заголовок, если существует
        if (Cookies.get('user')) {
            config.headers['email'] = Cookies.get('user');
        } else {
            config.headers['email'] = -1;
        }
        
        // Устанавливаем Content-Type по умолчанию
        if (!config.headers['Content-Type']) {
            config.headers['Content-Type'] = 'application/json';
        }
        
        return config;
    }
);
```

### 2. Упрощение кода на всех страницах

#### ✅ Before (документы)
```javascript
axios.get(DOCUMENTS_URL, { 
    headers: {
        'Content-Type': 'application/json',
        'token': Cookies.get('token') || -1,
        'email': Cookies.get('user') || -1
    },
})
```

#### ✅ After (документы)
```javascript
axios.get(DOCUMENTS_URL)
```

### 3. Упрощённые страницы

#### `src/pages/documents/index.js`
- **GET запрос**: Убрана явная передача `token` и `email`
- **DELETE запрос**: Убрана явная передача `token` и `email`
- **GET запрос (download)**: Убрана явная передача `token` и `email`

#### `src/pages/login/index.js`
- **POST запрос**: Упрощена передача параметров и заголовков

#### `src/pages/upload/index.js`
- **POST запрос**: Убраны ненужные заголовки

#### `src/pages/send-document/index.js`
- **GET запрос**: Убрана явная передача `token` и `email`

## Как это работает

```
                    ┌─────────────────────┐
                    │  Request Interceptor │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │ 1. Проверить cookies
                    │ 2. Добавить token
                    │ 3. Добавить email
                    │ 4. Поставить Content-Type
                    │
axios.get()  ────→  └──────────┬──────────┘  ────→  Backend
                               │
                         ┌─────▼────────┐
                         │ С заголовками:│
                         │ - token: xxxx │
                         │ - email: xxx  │
                         │ - Content-T.. │
                         └──────────────┘
```

## Преимущества

✅ **Меньше кода** - Не нужно писать заголовки в каждом запросе  
✅ **Консистентность** - Все запросы отправляют одинаковые заголовки  
✅ **Централизованная логика** - Если нужно изменить логику, меняется в одном месте  
✅ **DRY принцип** - Don't Repeat Yourself  
✅ **Простота** - Написание axios запросов стало проще и читабельнее  

## Примеры использования

### До (было писать это везде)
```javascript
import axios from '../../api/axios';
import Cookies from 'js-cookie';

// Загрузка документов
const result = await axios.get('/api/docs', {
    headers: {
        'token': Cookies.get('token') || -1,
        'email': Cookies.get('user') || -1,
        'Content-Type': 'application/json'
    }
});

// Удаление документа
await axios.delete('/api/docs', {
    params: { doc_id: 123 },
    headers: {
        'token': Cookies.get('token') || -1,
        'email': Cookies.get('user') || -1,
        'Content-Type': 'application/json'
    }
});
```

### После (теперь просто)
```javascript
import axios from '../../api/axios';

// Загрузка документов
const result = await axios.get('/api/docs');

// Удаление документа
await axios.delete('/api/docs', {
    params: { doc_id: 123 }
});
```

## Тестирование

1. Откройте DevTools (F12)
2. Перейдите на вкладку Network
3. Сделайте любой API запрос (например, загрузите документ)
4. Проверьте заголовки запроса - должны быть `token` и `email`

```
Headers:
  token: yourtoken123
  email: user@example.com
  Content-Type: application/json
```

## Заметки

- Интерцептор работает для всех видов HTTP запросов (GET, POST, PUT, DELETE, PATCH)
- Если `token` или `email` отсутствуют в cookies, отправляется значение `-1`
- `Content-Type` не переопределяется, если уже установлен
- Интерцептор прямой работает но прозрачно для кода
