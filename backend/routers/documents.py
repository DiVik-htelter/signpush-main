from fastapi import APIRouter

router_documents = APIRouter(prefix="/api/documents", tags=["Документы_new"])



#GET api/documents -- получение списка документов без содержимого
#GET api/documents/{id} -- получение содержимого 1 документа (по хорошему тут не бинарник, а ссылка на s3 хранилище должна быть)
#POST api/documents -- загрузка документа на сервер
#DELET api/documents/{id}
#GET api/documents/{id}/content -- для получения содержимого (можно было бы использовать один эндпоинт, но с разными заголовками, но тогда на фронтенде надо было бы заморачиваттся)

#POST /api/documents/{id}/signatures/visual
#POST /api/documents/{id}/signatures/unep
#GET /api/documents/{id}/signatures/{sign_id}/verify

@router_documents.get("",summary="Получение списка документов")
async def get_documents_list():
    """
    Получение списка документов без содержимого.
    """
    pass

@router_documents.get("/{id}",summary="Получение содержимого документа по ID")
async def get_document_by_id(id: int):
    """
    Получение документа по его ID.
    """
    pass

@router_documents.post("",summary="Загрузка документа на сервер")
async def upload_document():
    """
    Загрузка документа на сервер.
    """
    pass

@router_documents.delete("/{id}",summary="Удаление документа по ID")
async def delete_document_by_id(id: int):
    """
    Удаление документа по его ID.
    """
    pass

@router_documents.get("/{id}/content",summary="Скачивание документа по ID")
async def download_document_by_id(id: int):
    """
    Скачивание документа.
    """
    pass

@router_documents.post("/{id}/signatures/visual",summary="Подпись документа графически")
async def visual_sign_document(id: int):
    """
    Подпись документа графически.
    """
    pass

@router_documents.post("/{id}/signatures/unep",summary="Подпись документа УНЭП")
async def unep_sign_document(id: int):
    """
    Подпись документа УНЭП.
    """
    pass

@router_documents.get("/{id}/signatures/{sign_id}/verify",summary="Проверка подписи документа")
async def verify_document_signature(id: int, sign_id: int):
    """
    Проверка подписи документа.
    """
    pass