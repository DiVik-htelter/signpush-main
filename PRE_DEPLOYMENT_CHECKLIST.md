# ✅ Pre-Deployment Checklist для SignPush на VPS

## ПЕРЕД ДЕПЛОЕМ (проверьте на локальной машине)

- [ ] **Все контейнеры собираются локально**
  ```bash
  docker-compose build
  docker-compose up -d
  # Проверьте что всё работает
  curl http://localhost/
  ```

- [ ] **Frontend собирается без ошибок**
  ```bash
  npm install
  npm run build
  ```

- [ ] **Backend запускается**
  ```bash
  cd backend
  pip install -r requirements.txt
  python main.py
  # Должен запуститься на http://localhost:8000
  ```

- [ ] **База данных инициализируется**
  ```bash
  # Проверьте что full_dump.sql или schema существует
  ls -la backend/full_dump.sql
  ```

- [ ] **Все файлы committed в Git** (если используете Git)
  ```bash
  git status
  # Должно быть "nothing to commit"
  ```

---

## ПОДГОТОВКА VPS

- [ ] **VPS создан и доступен по SSH**
  ```bash
  ssh root@YOUR_VPS_IP
  ```

- [ ] **Минимум 2GB ОЗУ и 10GB дискового пространства**
  ```bash
  free -h
  df -h
  ```

- [ ] **Открыты необходимые порты**
  - [ ] Порт 22 (SSH)
  - [ ] Порт 80 (HTTP)
  - [ ] Порт 443 (HTTPS, если используете SSL)
  ```bash
  # Проверьте в админ-панели VPS провайдера
  ```

- [ ] **Домен (если нужен SSL)**
  - [ ] Домен зарегистрирован
  - [ ] DNS A record указывает на IP VPS
  ```bash
  nslookup YOUR_DOMAIN.com
  # Должен показать IP вашего VPS
  ```

---

## ПРОЦЕСС ДЕПЛОЯ

### Вариант 1: Через автоскрипт (рекомендуется)

```bash
ssh root@YOUR_VPS_IP

# Загрузите и запустите скрипт
curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/deploy.sh | bash

# Или если скрипт локальный:
scp deploy.sh root@YOUR_VPS_IP:/tmp/
ssh root@YOUR_VPS_IP "chmod +x /tmp/deploy.sh && /tmp/deploy.sh YOUR_DOMAIN.com"
```

### Вариант 2: Ручной деплой (следуйте DEPLOYMENT_GUIDE.md)

---

## ПРОВЕРКИ ПОСЛЕ ДЕПЛОЯ

- [ ] **Все контейнеры запущены**
  ```bash
  docker-compose ps
  # Все должны быть "Up"
  ```

- [ ] **Фронтенд загружается**
  ```bash
  curl -I http://YOUR_VPS_IP/ | head -5
  # Status: 200 OK
  ```

- [ ] **API работает**
  ```bash
  curl -X GET http://YOUR_VPS_IP/api/health
  # Должен вернуть какой-то результат
  ```

- [ ] **База данных инициализирована**
  ```bash
  docker-compose exec db psql -U signpush_user -d signpush_db -c "\dt"
  # Должны быть таблицы
  ```

- [ ] **Redis работает**
  ```bash
  docker-compose exec redis redis-cli ping
  # Должен ответить PONG
  ```

- [ ] **SSL сертификат установлен** (если используете домен)
  ```bash
  openssl s_client -connect YOUR_DOMAIN.com:443 -servername YOUR_DOMAIN.com < /dev/null 2>/dev/null | openssl x509 -noout -dates
  # Проверьте даты validity
  ```

- [ ] **HTTPS перенаправляет на https**
  ```bash
  curl -I http://YOUR_DOMAIN.com/ | head -1
  # Должен быть redirect на https
  ```

---

## РЕШЕНИЕ ТИПИЧНЫХ ПРОБЛЕМ

### ❌ "Connection refused" на фронтенде
```bash
# Проверьте логи nginx
docker-compose logs nginx

# Пересоберите образ
docker-compose build --no-cache nginx
docker-compose restart nginx
```

### ❌ "Backend не подключается к БД"
```bash
# Проверьте переменные окружения
docker-compose exec backend env | grep DATABASE_URL

# Проверьте статус БД
docker-compose logs db

# Убедитесь что пароли совпадают в .env файлах
cat .env
cat backend/.env
```

### ❌ "Port 80 already in use"
```bash
# Проверьте что занимает порт
netstat -tlnp | grep :80

# Остановите конфликтующий сервис или измените порт в docker-compose.yml
```

### ❌ "SSL сертификат not found"
```bash
# Запустите certbot
certbot certonly --standalone -d YOUR_DOMAIN.com -d www.YOUR_DOMAIN.com

# Обновите конфиг nginx/default.conf
# Перезагрузите nginx
docker-compose restart nginx
```

### ❌ "Out of disk space"
```bash
# Очистите старые Docker образы
docker image prune -a

# Очистите dangling volumes
docker volume prune

# Проверьте место
du -sh /var/lib/docker/
```

---

## МОНИТОРИНГ В ПРОДАКШЕНЕ

### Регулярные проверки

```bash
# Укажите в crontab (каждый час)
0 * * * * docker-compose -f /opt/signpush/docker-compose.yml ps | grep -q "Up" || echo "Containers down!" | mail -s "SignPush Alert" admin@example.com
```

### Просмотр логов

```bash
# Реал-тайм логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs backend

# Последние 100 строк
docker-compose logs --tail=100 backend

# Логи за последний час
docker-compose logs --since 1h backend
```

### Backup базы данных

```bash
# Ручной backup
docker-compose exec -T db pg_dump -U signpush_user signpush_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Или используйте скрипт backup.sh (см. DEPLOYMENT_GUIDE.md)
/opt/signpush/backup.sh
```

---

## ФИНАЛЬНЫЕ ШАГИ

- [ ] **Протестируйте полный цикл использования**
  - Загрузка документа
  - Подпись документа
  - Скачивание подписанного документа

- [ ] **Проверьте логи на ошибки**
  ```bash
  docker-compose logs | grep -i "error"
  ```

- [ ] **Документируйте для вашей команды**
  - Хост и порт приложения
  - Пароль для администратора (если есть)
  - Контакты поддержки

- [ ] **Настройте мониторинг/алерты**
  - Отключение контейнеров
  - Нехватка свободного места
  - Критические ошибки в логах

- [ ] **Создайте первый backup**
  ```bash
  docker-compose exec -T db pg_dump -U signpush_user signpush_db > initial_backup.sql
  scp root@YOUR_VPS_IP:/opt/signpush/initial_backup.sql ./backups/
  ```

---

## 🎉 ГОТОВО!

Ваше приложение SignPush должно работать на VPS. 

Для поддержки обновлений и новых версий:
```bash
cd /opt/signpush
git pull
docker-compose build --no-cache
docker-compose up -d
```

Удачи! 🚀
