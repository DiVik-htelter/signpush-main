# Stage 1: Сборка React
FROM node:18-alpine as build-stage

WORKDIR /app

# Копируем package.json и устанавливаем зависимости
COPY package*.json ./
RUN npm install

# Копируем исходный код и собираем проект
COPY . .
RUN npm run build

# Результат сборки будет в папке /app/build