# Stage 1: Сборка фронтенда
FROM node:18-alpine AS build-stage
WORKDIR /app

COPY ./package*.json ./
RUN npm install

COPY ./public ./public
COPY ./src ./src
COPY ./.env* ./

RUN npm run build

# Stage 2: Раздача статики через Nginx
FROM nginx:stable-alpine
COPY --from=build-stage /app/build /usr/share/nginx/html
# default.conf будет загружаться из volume в docker-compose
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

