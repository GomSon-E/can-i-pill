FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
ARG BACKEND_HOST=backend
COPY --from=builder /app/dist /var/www/can-i-pill
COPY nginx.conf /tmp/default.conf.template
RUN sed "s/__BACKEND_HOST__/${BACKEND_HOST}/g" /tmp/default.conf.template > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
