GET api/users/ -- аутентификация
GET api/users/{id} -- получение данные о конкретном юзере
POST api/users/ -- регистрация (создание) пользователя
PATCH  api/users/ -- обновление токена пользователя
GET api/users/yandex/  -- регистрация через яндекс
PATCH api/users/{id} -- 
POST api/users/{id}/keys -- генерация ключевой пары
GET api/users/{id}/keys -- получение публичного ключа



HEAD api/documents/ -- получение списка документов без содержимого
GET api/documents/{id} -- получение содержимого 1 документа (по хорошему тут не бинарник, а ссылка на s3 хранилище должна быть)
POST api/documents/ -- загрузка документа на сервер
DELET api/documents/{id}
GET api/documents/{id}/content -- для получения содержимого (можно было бы использовать один эндпоинт, но с разными заголовками, но тогда на фронтенде надо было бы заморачиваттся)

POST /api/documents/{id}/signatures/visual
POST /api/documents/{id}/signatures/unep
GET /api/documents/{id}/signatures/{sign_id}/verify

и открытые эндпоинты на 1С