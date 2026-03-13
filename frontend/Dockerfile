FROM node:18-alpine AS builder

WORKDIR /app

# 依存関係のコピーとインストール
COPY package*.json ./
RUN npm ci

# ソースコードのコピーとビルド
COPY . .
RUN npm run build

# 本番用サーバー
FROM nginx:alpine AS frontend

# ビルド成果物をnginxにコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx設定ファイルをコピー
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]