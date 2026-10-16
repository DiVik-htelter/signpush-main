from fastapi import APIRouter

router_auth = APIRouter(prefix="/api/auth", tags=["Аутентификацияzzz"])


@router_auth.post("/login",summary="Аутентификация пользователя")
async def authenticate_user():
    """
    Аутентификация пользователя.
    """
    pass

@router_auth.post("/token",summary="Обновление токена пользователя")
async def update_token():
    """
    Обновление токена пользователя.
    """
    pass

@router_auth.get("/yandex",summary="Аутентификация пользователя через Яндекс")
async def authenticate_yandex():
    """
    Аутентификация пользователя через яндекс.
    """
    pass