# Гайд по деплою SignPush на VPS

## Предварительные требования
- VPS с Ubuntu 20.04+ или Debian
- SSH доступ к серверу
- Домен (опционально, но рекомендуется)
- Минимум 2GB ОЗУ, 10GB дискового пространства

---

## ШАГИ ДЕПЛОЯ

### ШАГ 1: Подготовка VPS сервера

#### 1.1 Подключитесь к VPS по SSH
```bash
ssh root@YOUR_VPS_IP
```

#### 1.2 Обновите пакеты
```bash
apt-get update && apt-get upgrade -y
```

#### 1.3 Установите Docker
```bash
apt-get install -y docker.io
systemctl start docker
systemctl enable docker
```

#### 1.4 Установите Docker Compose
```bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

#### 1.5 Создайте рабочую директорию
```bash
mkdir -p /opt/signpush
cd /opt/signpush
```

---

### ШАГ 2: Загрузите код приложения на VPS

**Вариант A: Через Git (если есть репозиторий)**
```bash
cd /opt/signpush
git clone https://github.com/YOUR_USERNAME/signpush-main.git .
```

**Вариант B: Через SCP (скопировать со своего компьютера)**
```bash
# Выполните на локальном компьютере:
scp -r d:\4_cours\diplom\signpush-main/* root@YOUR_VPS_IP:/opt/signpush/
```

Проверьте, что всё загруженно:
```bash
ls -la /opt/signpush/
# Должны быть: docker-compose.yml, Dockerfile, backend/, src/, package.json и т.д.
```

---

### ШАГ 3: Подготовка файлов конфигурации

#### 3.1 Создайте корневой .env (рядом с docker-compose.yml)
```bash
cat > /.env << 'EOF'
# Параметры БД
DB_USER=postgres
DB_PASSWORD=1234
DB_NAME=signpush
DB_HOST=db
DB_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
# Параметры приложения (для backend)
DEBUG=false
ENVIRONMENT=production
EOF
```




STRONG_PASSWORD_HERE_CHANGE_ME = qNS83GSEI9i6iReP

**⚠️ ВАЖНО:** Замените `STRONG_PASSWORD_HERE_CHANGE_ME` на надежный пароль!

#### 3.2 Создайте backend/.env
```bash
cat > /opt/signpush/backend/.env << 'EOF'
# Подключение к БД (используется контейнером backend)
POSTGRES_USER=signpush_user
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE_CHANGE_ME
POSTGRES_DB=signpush_db
DATABASE_URL=postgresql://signpush_user:STRONG_PASSWORD_HERE_CHANGE_ME@db:5432/signpush_db

# Redis
REDIS_URL=redis://redis:6379/0

# FastAPI
SECRET_KEY=your-super-secret-key-change-me-in-production
DEBUG=false
ENVIRONMENT=production
EOF
```

**⚠️ ВАЖНО:** Используйте ОДИНАКОВЫЕ пароли в обоих файлах!

---

### ШАГ 4: Настройте Nginx для продакшена (HTTPS + домен)

#### 4.1 Если у вас есть домен - обновите конфиг Nginx

```bash
cat > signpush-main/nginx/default.conf << 'EOF'
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=5r/s;

server {
    listen 80;
    server_name sign-push.ru;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sign-push.ru;

    # SSL сертификаты (будут установлены Certbot)
    ssl_certificate /etc/letsencrypt/live/sign-push.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sign-push.ru/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 20M;
    
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/pdf;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # PDF.js кэш
    location /pdfjs-dist/ {
        root /usr/share/nginx/html;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # API
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # M2M API
    location /api/v1/ {
        if ($http_x_signpush_key != "super-secret-pki-token") {
            return 403;
        }
        
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    error_page 404 /index.html;
}
EOF
```

**⚠️ ВАЖНО:** Замените `sign-push.ru` на ваш реальный домен!

#### 4.2 Если домена нет - оставьте конфиг как есть (HTTP на порту 80)

---

### ШАГ 5: Установка SSL сертификата (Certbot + Let's Encrypt)

**Только если у вас ЕСТЬ домен:**

```bash
# Установите Certbot
apt-get install -y certbot python3-certbot-nginx

# Создайте сертификат (замените sign-push.ru)
certbot certonly --standalone -d sign-push.ru -d www.sign-push.ru --email zena252010@gmail.com --agree-tos --non-interactive
```

Это создаст сертификаты в `/etc/letsencrypt/live/sign-push.ru/`

**Автоматическое обновление:**
```bash
# Проверьте таймер
systemctl list-timers | grep certbot

# Если не настроено, добавьте в crontab
crontab -e
# Добавьте строку:
0 3 * * * certbot renew --quiet
```

---

### ШАГ 6: Запуск контейнеров

#### 6.1 Перейдите в директорию проекта
```bash
cd /opt/signpush
```

#### 6.2 Запустите docker-compose
```bash
docker-compose up -d
```

#### 6.3 Проверьте статус контейнеров
```bash
docker-compose ps
```

Должны быть в состоянии `Up`:
- `signpush_db` (PostgreSQL)
- `signpush_redis` (Redis)
- `signpush_backend` (FastAPI)
- `signpush_nginx` (Nginx)

#### 6.4 Проверьте логи (если что-то не работает)
```bash
# Общие логи
docker-compose logs

# Логи конкретного сервиса
docker-compose logs backend
docker-compose logs db
docker-compose logs nginx
```

---

### ШАГ 7: Проверка доступности

#### 7.1 Если использовали домен с SSL
```bash
curl -k https://sign-push.ru/
```

#### 7.2 Если используете IP или no-SSL
```bash
curl http://YOUR_VPS_IP/
```

Должны увидеть HTML страницу React приложения (или ошибка 404, если что-то с сборкой фронтенда)

#### 7.3 Проверьте API
```bash
curl http://YOUR_VPS_IP/api/health
# или
curl https://sign-push.ru/api/health
```

---

### ШАГ 8: Настройка автозапуска контейнеров при перезагрузке сервера

```bash
# Включите автозапуск Docker при рестарте сервера
systemctl enable docker

# Отредактируйте docker-compose.yml (уже сделано)
# Проверьте что все сервисы имеют "restart: always"
grep -A 1 "restart:" /opt/signpush/docker-compose.yml
```

---

### ШАГ 9: Регулярные backups БД (опционально, но рекомендуется)

#### 9.1 Создайте скрипт backup
```bash
cat > /opt/signpush/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/signpush/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/signpush_db_$DATE.sql"

docker-compose exec -T db pg_dump -U signpush_user signpush_db > $BACKUP_FILE

# Удалите старые backups (старше 30 дней)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete

echo "Backup created: $BACKUP_FILE"
EOF

chmod +x /opt/signpush/backup.sh
```

#### 9.2 Добавьте в crontab (раз в сутки в 2 часа ночи)
```bash
crontab -e
# Добавьте:
0 2 * * * cd /opt/signpush && ./backup.sh
```

---

## ФИНАЛЬНАЯ ПРОВЕРКА

```bash
# Всё ли запущено?
docker-compose ps

# Чистая ли база? (должны быть таблицы)
docker-compose exec db psql -U signpush_user -d signpush_db -c "\dt"

# Работает ли фронтенд?
curl -I http://YOUR_VPS_IP/ | head -1

# Работает ли API?
docker-compose logs backend | tail -20
```

---

## ВОЗМОЖНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема: "Nginx не может найти фронтенд"
**Решение:** Пересоберите образы
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Проблема: "Backend не подключается к БД"
**Решение:** Проверьте переменные в `.env` и совпадают ли пароли
```bash
docker-compose logs backend | grep -i "database\|connection"
```

### Проблема: "Port 80/443 уже занят"
**Решение:** Проверьте/остановите другие сервисы
```bash
netstat -tlnp | grep -E ":80|:443"
# Если занято, снимите конфликтующий сервис или измените порт в docker-compose.yml
```

### Проблема: "SSL сертификат не найден"
**Решение:** Запустите Certbot снова
```bash
certbot certonly --standalone -d sign-push.ru --email YOUR_EMAIL@example.com --agree-tos --non-interactive
```

---

## ОБНОВЛЕНИЕ ПРИЛОЖЕНИЯ

Когда выкатываете новую версию:

```bash
cd /opt/signpush

# Обновите код (если используете Git)
git pull

# Пересоберите образы
docker-compose build --no-cache

# Перезапустите контейнеры
docker-compose up -d

# Проверьте статус
docker-compose ps
```

---

## УДАЛЕНИЕ (если нужно очистить всё)

```bash
cd /opt/signpush
docker-compose down -v  # "-v" удалит также volumes с БД!
rm -rf /opt/signpush
```

⚠️ Это удалит ВСЕ данные! Сначала сделайте backup!

---

## КОНТАКТЫ ДЛЯ ПОМОЩИ

Если что-то не работает:
1. Проверьте логи: `docker-compose logs`
2. Убедитесь что .env файлы заполнены правильно
3. Проверьте открыты ли порты: `netstat -tlnp`
4. Убедитесь что хватает ОЗУ и дискового пространства: `free -h`, `df -h`
