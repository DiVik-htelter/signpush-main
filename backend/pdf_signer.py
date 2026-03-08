"""
Модуль для работы с PDF документами и встраивания визуальных подписей.

Использует PyMuPDF (fitz) для манипуляции с PDF файлами.
Позволяет встраивать изображения подписей в указанные позиции на страницах PDF.
"""

import fitz  # PyMuPDF
import base64
from io import BytesIO
from typing import Tuple


def add_signature_to_pdf(
    pdf_base64: str,
    signature_base64: str,
    page_number: int,
    x: float,
    y: float,
    width: float,
    height: float
    ) -> Tuple[str, bool]:
    """
    Встраивает визуальную подпись в PDF документ.
    
    Метод принимает PDF и изображение подписи в формате base64,
    размещает подпись в указанной позиции на указанной странице,
    и возвращает подписанный PDF также в base64.
    
    Args:
        pdf_base64: PDF документ в формате base64 (может содержать data URI префикс)
        signature_base64: Изображение подписи в base64 (PNG/JPG)
        page_number: Номер страницы для размещения подписи (0-indexed)
        x: Координата X левого верхнего угла подписи (в пикселях canvas)
        y: Координата Y левого верхнего угла подписи (в пикселях canvas)
        width: Ширина подписи в пикселях
        height: Высота подписи в пикселях
        
    Returns:
        Tuple[str, bool]: (Подписанный PDF в base64, флаг успеха)
        
    Raises:
        Exception: При ошибках работы с PDF или изображением
    """
    try:
        print(f"[INFO] Starting PDF signing process...")
        print(f"[INFO] Page: {page_number}, Position: ({x}, {y}), Size: ({width}x{height})")
        
        # Очищаем base64 строки от data URI префиксов
        # Пример: "data:application/pdf;base64,..." -> только base64 часть
        if 'base64,' in pdf_base64:
            pdf_clean = pdf_base64.split('base64,')[-1]
        else:
            pdf_clean = pdf_base64
            
        if 'base64,' in signature_base64:
            signature_clean = signature_base64.split('base64,')[-1]
        else:
            signature_clean = signature_base64
        
        # Декодируем PDF из base64 в байты
        pdf_bytes = base64.b64decode(pdf_clean)
        print(f"[INFO] PDF decoded, size: {len(pdf_bytes)} bytes")
        
        # Открываем PDF документ из байтов
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        print(f"[INFO] PDF opened successfully, total pages: {pdf_document.page_count}")
        
        # Проверяем валидность номера страницы
        if page_number < 0 or page_number >= pdf_document.page_count:
            raise ValueError(f"Invalid page number: {page_number}. Document has {pdf_document.page_count} pages.")
        
        # Декодируем изображение подписи из base64
        signature_bytes = base64.b64decode(signature_clean)
        print(f"[INFO] Signature image decoded, size: {len(signature_bytes)} bytes")
        
        # Получаем нужную страницу PDF
        page = pdf_document[page_number]
        page_height = page.rect.height
        page_width = page.rect.width
        print(f"[INFO] Page dimensions: {page_width}x{page_height}")
        
        # ВАЖНО: Конвертация координат из Canvas в PDF координаты
        # Canvas использует координаты от верхнего левого угла (0,0)
        # PDF (fitz) использует координаты от нижнего левого угла
        # Также нужно учесть масштабирование между canvas и PDF
        
        # Предполагаем, что canvas масштабирован с scale=2.5 (как в pdf-reader.js)
        scale_factor = 2.5
        
        # Конвертируем координаты canvas в координаты PDF
        pdf_x = x / scale_factor
        pdf_y = y / scale_factor
        pdf_width = width / scale_factor
        pdf_height = height / scale_factor
        
        # Создаем прямоугольник для размещения подписи
        # fitz.Rect(x0, y0, x1, y1) где (x0,y0) - левый верхний, (x1,y1) - правый нижний
        rect = fitz.Rect(
            pdf_x,                      # левая граница
            pdf_y,                      # верхняя граница
            pdf_x + pdf_width,          # правая граница
            pdf_y + pdf_height          # нижняя граница
        )
        
        print(f"[INFO] Signature will be placed at PDF rect: {rect}")
        
        # Вставляем изображение подписи на страницу
        # stream - байты изображения
        # overlay=True - размещаем поверх существующего контента
        page.insert_image(rect, stream=signature_bytes, overlay=True)
        print(f"[INFO] Signature image inserted successfully")
        
        # Сохраняем измененный PDF в буфер памяти
        output_buffer = BytesIO()
        pdf_document.save(
            output_buffer,
            garbage=4,          # Максимальная очистка неиспользуемых объектов
            deflate=True,       # Сжатие для уменьшения размера
            clean=True          # Очистка и оптимизация PDF
        )
        pdf_document.close()
        print(f"[INFO] PDF document saved and closed")
        
        # Получаем байты из буфера
        output_buffer.seek(0)
        signed_pdf_bytes = output_buffer.read()
        print(f"[INFO] Signed PDF size: {len(signed_pdf_bytes)} bytes")
        
        # Конвертируем обратно в base64 с data URI префиксом
        signed_pdf_base64 = base64.b64encode(signed_pdf_bytes).decode('utf-8')
        result = f"data:application/pdf;base64,{signed_pdf_base64}"
        
        print(f"[INFO] PDF signing completed successfully")
        return result, True
        
    except Exception as e:
        print(f"[ERROR] Error during PDF signing: {e}")
        import traceback
        traceback.print_exc()
        return "", False


def validate_signature_params(page_number: int, x: float, y: float, 
                                width: float, height: float) -> Tuple[bool, str]:
    """
    Валидирует параметры подписи перед встраиванием.
    
    Args:
        page_number: Номер страницы
        x, y: Координаты позиции
        width, height: Размеры подписи
        
    Returns:
        Tuple[bool, str]: (Валидна ли подпись, сообщение об ошибке)
    """
    if page_number < 0:
        return False, "Page number must be non-negative"
        
    if width <= 0 or height <= 0:
        return False, "Width and height must be positive"
        
    if x < 0 or y < 0:
        return False, "Coordinates must be non-negative"
        
    return True, "OK"
