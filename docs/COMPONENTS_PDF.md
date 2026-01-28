# 🧩 Анализ компонентов: PdfReader

## Содержание
1. [Обзор компонента](#1-обзор-компонента)
2. [Состояние и lifecycle](#2-состояние-и-lifecycle)
3. [PDF.js интеграция](#3-pdfjs-интеграция)
4. [Рисование подписи](#4-рисование-подписи)
5. [Проблемы и рефакторинг](#5-проблемы-и-рефакторинг)

---

## 1. Обзор компонента

**Файл:** `src/components/pdf-reader/pdf-reader.js` (261 строка)

### Назначение
Полнофункциональный просмотрщик PDF с возможностью:
- Рендеринга PDF на canvas
- Навигации по страницам
- Выбора области для подписи
- Размещения рукописной подписи
- Отправки подписанного документа на сервер

### Основные функции
```javascript
function PdfReader({file}) {
    // 1. Рендеринг PDF из Base64
    // 2. Пагинация страниц
    // 3. Выбор области мышью (drag & drop)
    // 4. Интеграция SignatureModal
    // 5. Рисование подписи на canvas
    // 6. POST запрос с подписанным документом
}
```

### Архитектура
```
PdfReader
├── PDF.js Worker (рендеринг в фоне)
├── Canvas (отображение страницы)
├── SignatureModal (создание подписи)
├── Mouse Events (выбор области)
└── API Integration (отправка документа)
```

---

## 2. Состояние и lifecycle

### State переменные
```javascript
const [pdf, setPdf] = useState(null);                    // PDF документ
const [pageNumber, setPageNumber] = useState(1);         // Текущая страница
const [numPages, setNumPages] = useState(null);          // Всего страниц
const [isMouseDown, setIsMouseDown] = useState(false);   // Флаг drag
const [start, setStart] = useState({x: 0, y: 0});       // Начало выбора
const [end, setEnd] = useState({x: 0, y: 0});           // Конец выбора
const [showSignModal, setShowSignModal] = useState(false);
const [signatureUrl, setSignatureUrl] = useState('');    // Base64 подписи
const [cookies] = useCookies(['token']);
```

### useEffect для загрузки PDF

```javascript
useEffect(() => {
    const loadPdf = async () => {
        try {
            pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;
            
            const loadingTask = pdfjsLib.getDocument(file);
            const pdfDoc = await loadingTask.promise;
            
            setPdf(pdfDoc);
            setNumPages(pdfDoc.numPages);
            renderPage(pdfDoc, 1);
        } catch (error) {
            console.error('Error loading PDF:', error);
        }
    };

    if (file) {
        loadPdf();
    }
}, [file]);
```

**Проблемы:**
- ❌ Нет cleanup для PDF документа
- ❌ Отсутствует loading state
- ❌ Слабая обработка ошибок

### useEffect для event listeners

```javascript
useEffect(() => {
    const canvas = canvasRef.current;
    
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    
    // ❌ MEMORY LEAK: Нет cleanup!
}, []);
```

**✅ Правильно:**
```javascript
useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    
    return () => {
        canvas.removeEventListener('mousedown', handleMouseDown);
        canvas.removeEventListener('mousemove', handleMouseMove);
        canvas.removeEventListener('mouseup', handleMouseUp);
    };
}, []);
```

---

## 3. PDF.js интеграция

### Инициализация Worker

```javascript
import * as pdfjsLib from 'pdfjs-dist/build/pdf';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.entry';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;
```

**Зачем Worker:**
- Рендеринг PDF в отдельном потоке
- Не блокирует UI
- Лучшая производительность

### Загрузка документа

```javascript
const loadingTask = pdfjsLib.getDocument(file);  // file = Base64
const pdfDoc = await loadingTask.promise;

console.log('Pages:', pdfDoc.numPages);
```

### Рендеринг страницы

```javascript
const renderPage = async (pdfDoc, pageNum) => {
    const page = await pdfDoc.getPage(pageNum);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const viewport = page.getViewport({scale: 1.5});
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    const renderContext = {
        canvasContext: ctx,
        viewport: viewport
    };
    
    await page.render(renderContext).promise;
};
```

**Параметры:**
- `scale: 1.5` — увеличение для лучшего качества
- `viewport` — размеры страницы с учетом масштаба
- `renderContext` — конфигурация рендеринга

### Навигация по страницам

```javascript
const goToPreviousPage = () => {
    if (pageNumber > 1) {
        const newPageNumber = pageNumber - 1;
        setPageNumber(newPageNumber);
        renderPage(pdf, newPageNumber);
    }
};

const goToNextPage = () => {
    if (pageNumber < numPages) {
        const newPageNumber = pageNumber + 1;
        setPageNumber(newPageNumber);
        renderPage(pdf, newPageNumber);
    }
};
```

---

## 4. Рисование подписи

### Выбор области мышью

```javascript
const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setStart({x, y});
    setEnd({x, y});
    setIsMouseDown(true);
};

const handleMouseMove = (e) => {
    if (!isMouseDown) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setEnd({x, y});
    drawRect(start.x, start.y, x - start.x, y - start.y);
};

const handleMouseUp = () => {
    setIsMouseDown(false);
    setShowSignModal(true);  // Открыть модалку подписи
};
```

### Рисование прямоугольника

```javascript
const drawRect = (x, y, width, height) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Перерисовать страницу (очистить старый rect)
    renderPage(pdf, pageNumber);
    
    // Нарисовать новый rect
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, width, height);
};
```

**Проблема:** Каждый раз перерисовывается вся страница!

**✅ Оптимизация:**
```javascript
// Использовать два canvas
const tempCanvas = document.createElement('canvas');
const tempCtx = tempCanvas.getContext('2d');

// Основной canvas - PDF
// tempCanvas - overlay для rect
```

### Размещение подписи

```javascript
const handleCallback = (signatureDataUrl) => {
    setSignatureUrl(signatureDataUrl);
    
    const img = new Image();
    img.src = signatureDataUrl;
    
    img.onload = () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
        const width = end.x - start.x;
        const height = end.y - start.y;
        
        ctx.drawImage(img, start.x, start.y, width, height);
    };
};
```

### Отправка на сервер

```javascript
const handleSendSignature = async () => {
    const canvas = canvasRef.current;
    const signedPdfBase64 = canvas.toDataURL('image/png');
    
    try {
        const response = await axios.post(
            'https://test.signpush.ru/api/v4.1/paper/document',
            {
                title: 'Signed Document',
                base64: signedPdfBase64,
                // ... другие поля
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'apiKey': '2e4ee...',
                    'token': cookies.token
                }
            }
        );
        
        if (response.data.status === 0) {
            alert('Документ успешно подписан!');
        }
    } catch (error) {
        console.error('Error sending signature:', error);
        alert('Ошибка при отправке документа');
    }
};
```

**Проблема:** Отправляется PNG скриншот canvas, а не PDF!

---

## 5. Проблемы и рефакторинг

### Критические проблемы

**🚨 Memory leak - event listeners:**
```javascript
useEffect(() => {
    canvas.addEventListener('mousedown', handleMouseDown);
    // ❌ Нет removeEventListener в cleanup
}, []);
```

**🚨 Hardcoded API key (снова):**
```javascript
'apiKey': '2e4ee3528082873f6407f3a42a85854156bef0b0ccb8336fd8843a3f13e2ff09'
```

**🚨 Отправка PNG вместо PDF:**
```javascript
const signedPdfBase64 = canvas.toDataURL('image/png');
// Нужно использовать pdf-lib для модификации PDF
```

### Средние проблемы

**⚠️ Компонент слишком большой (261 строка):**
Нужно разбить на подкомпоненты:
```
PdfReader
├── PdfViewer (рендеринг)
├── PageNavigation (навигация)
├── SignatureSelector (выбор области)
└── SignatureUploader (отправка)
```

**⚠️ Нет обработки ошибок:**
```javascript
try {
    const pdfDoc = await loadingTask.promise;
} catch (error) {
    console.error('Error loading PDF:', error);
    // ❌ Пользователь не видит ошибку
}
```

**⚠️ Перерисовка всей страницы при drag:**
```javascript
const drawRect = () => {
    renderPage(pdf, pageNumber);  // Expensive!
    ctx.strokeRect(x, y, width, height);
};
```

### Рекомендации по рефакторингу

**1. Разделить на подкомпоненты:**
```javascript
// PdfViewer.js - рендеринг PDF
// SignatureArea.js - выбор области
// SignatureControls.js - кнопки управления
```

**2. Использовать pdf-lib для подписи:**
```javascript
import { PDFDocument } from 'pdf-lib';

const pdfDoc = await PDFDocument.load(file);
const pages = pdfDoc.getPages();
const firstPage = pages[0];

const pngImage = await pdfDoc.embedPng(signatureDataUrl);
firstPage.drawImage(pngImage, {
    x: start.x,
    y: start.y,
    width: end.x - start.x,
    height: end.y - start.y
});

const pdfBytes = await pdfDoc.save();
// Отправить на сервер
```

**3. Добавить loading и error states:**
```javascript
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

if (loading) return <Spinner />;
if (error) return <ErrorMessage error={error} />;
```

**4. Оптимизировать рендеринг:**
```javascript
// Использовать два canvas
<canvas ref={pdfCanvasRef} />     {/* PDF */}
<canvas ref={overlayCanvasRef} /> {/* Rect */}
```

**5. Исправить memory leaks:**
```javascript
useEffect(() => {
    // Add listeners
    
    return () => {
        // Remove listeners
        // Cleanup PDF document
        pdf?.destroy();
    };
}, [pdf]);
```

### Улучшенная архитектура

```javascript
// components/pdf-reader/
├── PdfReader.js           // Основной контейнер
├── PdfCanvas.js          // Рендеринг PDF
├── SignatureSelector.js  // Выбор области
├── PageControls.js       // Навигация
└── usePdf.js            // Custom hook для PDF.js

// hooks/usePdf.js
export const usePdf = (file) => {
    const [pdf, setPdf] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        // Load PDF logic
        
        return () => {
            pdf?.destroy();
        };
    }, [file]);
    
    return {pdf, loading, error};
};
```

---

## Заключение

### Сильные стороны
- ✅ Интеграция PDF.js с Web Workers
- ✅ Интерактивный выбор области
- ✅ Рукописная подпись с canvas

### Критические проблемы
- 🚨 Memory leak (event listeners не удаляются)
- 🚨 Отправка PNG вместо подписанного PDF
- 🚨 Hardcoded API key

### Рекомендации
1. **Немедленно:** Исправить memory leak
2. **Высокий:** Использовать pdf-lib для подписи PDF
3. **Средний:** Разбить на подкомпоненты (261 строка → 4-5 файлов по 50-80 строк)
4. **Низкий:** Оптимизировать рендеринг с двумя canvas

### Приоритет рефакторинга: 🟠 Высокий
