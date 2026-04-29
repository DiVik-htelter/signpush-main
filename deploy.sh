#!/bin/bash

# ============================================================================
# Автоматизированный скрипт деплоя SignPush на VPS
# Запустите: curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/deploy.sh | bash
# ============================================================================

set -e

echo "=========================================="
echo "SignPush VPS Deployment Script"
echo "=========================================="

# Проверка прав администратора
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен от root (используйте sudo)"
   exit 1
fi

# Параметры
APP_DIR="/opt/signpush"
DOMAIN="${1:-localhost}"
DB_PASSWORD="${2:-signpush_secure_password_2024}"

echo ""
echo "🔧 Параметры деплоя:"
echo "  - Директория: $APP_DIR"
echo "  - Домен: $DOMAIN"
echo "  - Пароль БД: ***"
echo ""

# ШАГ 1: Обновление системы
echo "📦 [1/7] Обновление пакетов..."
apt-get update -qq
apt-get upgrade -y -qq

# ШАГ 2: Установка Docker
echo "🐳 [2/7] Установка Docker..."
if ! command -v docker &> /dev/null; then
    apt-get install -y -qq docker.io
    systemctl start docker
    systemctl enable docker
else
    echo "   ✓ Docker уже установлен"
fi

# ШАГ 3: Установка Docker Compose
echo "📝 [3/7] Установка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "   ✓ Docker Compose уже установлен"
fi

# ШАГ 4: Подготовка директории
echo "📁 [4/7] Подготовка директории приложения..."
mkdir -p $APP_DIR
cd $APP_DIR

# ШАГ 5: Создание файлов окружения
echo "⚙️  [5/7] Создание файлов конфигурации..."

# Корневой .env
cat > $APP_DIR/.env << EOF
DB_USER=signpush_user
DB_PASSWORD=$DB_PASSWORD
DB_NAME=signpush_db
SECRET_KEY=signpush-secret-key-$(openssl rand -hex 16)
DEBUG=false
ENVIRONMENT=production
EOF

# Backend .env
mkdir -p $APP_DIR/backend
cat > $APP_DIR/backend/.env << EOF
POSTGRES_USER=signpush_user
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=signpush_db
DATABASE_URL=postgresql://signpush_user:$DB_PASSWORD@db:5432/signpush_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=signpush-secret-key-$(openssl rand -hex 16)
DEBUG=false
ENVIRONMENT=production
EOF

echo "   ✓ Файлы конфигурации созданы"

# ШАГ 6: Запуск docker-compose
echo "🚀 [6/7] Запуск контейнеров..."
docker-compose down 2>/dev/null || true
docker-compose pull
docker-compose build --no-cache
docker-compose up -d

# Ожидание инициализации БД
echo "⏳ Ожидание инициализации БД (30 сек)..."
sleep 30

# ШАГ 7: Проверка статуса
echo "✅ [7/7] Проверка статуса..."
docker-compose ps

echo ""
echo "=========================================="
echo "✅ Деплой завершен!"
echo "=========================================="
echo ""
echo "📍 Доступ к приложению:"

if [ "$DOMAIN" != "localhost" ]; then
    echo "   🌐 https://$DOMAIN"
    echo ""
    echo "⚠️  ВНИМАНИЕ: Убедитесь что:"
    echo "   1. Домен $DOMAIN указывает на этот VPS"
    echo "   2. Запустите: certbot certonly --standalone -d $DOMAIN"
    echo "   3. Обновите конфиг: nginx/default.conf с вашим доменом"
    echo "   4. Перезагрузите nginx: docker-compose restart nginx"
else
    echo "   🌐 http://$(hostname -I | awk '{print $1}')"
fi

echo ""
echo "📋 Полезные команды:"
echo "   - Логи:          docker-compose logs -f [service]"
echo "   - Статус:        docker-compose ps"
echo "   - Перезагрузка:  docker-compose restart"
echo "   - Остановка:     docker-compose down"
echo ""
