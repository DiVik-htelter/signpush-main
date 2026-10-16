from fastapi import APIRouter

router_users = APIRouter(prefix="/api/users", tags=["Пользователи"])


# эндпоинты юзера
#GET api/users/ -- аутентификация
#GET api/users/{id} -- получение данные о конкретном юзере
#POST api/users/ -- регистрация (создание) пользователя
#PATCH  api/users/ -- обновление токена пользователя
#GET api/users/yandex/  -- регистрация через яндекс
#PATCH api/users/{id} -- обновление (изменение) данные пользователя
#POST api/users/{id}/keys -- генерация ключевой пары
#GET api/users/{id}/keys -- получение публичного ключа



@router_users.get("/{id}",summary="Получение данных о конкретном пользователе")
async def get_user(id: int):
    """
    Получение данных о конкретном пользователе.
    """
    pass

@router_users.post("",summary="Регистрация пользователя")
async def register_user():
    """
    Регистрация пользователя.
    """
    pass

@router_users.patch("/{id}",summary="Обновление данных пользователя")
async def update_user(id: int):
    """
    Обновление данных пользователя.
    """
    pass

@router_users.get("/{id}/keys",summary="Получение публичного ключа пользователя")
async def get_user_public_key(id: int):
    """
    Получение публичного ключа пользователя.
    """
    pass

@router_users.post("/{id}/keys",summary="Генерация публичного ключа пользователя")
async def generate_user_public_key(id: int):
    """
    Генерация публичного ключа пользователя.
    """
    pass