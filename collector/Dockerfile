FROM python:3.11-slim AS builder

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    cron \
    && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/sbin/cron /usr/sbin/crond

# Python依存関係のコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# cronジョブの設定
RUN echo "0 9,13 * * * cd /app && python collector.py >> /var/log/cron.log 2>&1" > /etc/cron.d/hojo-collector
RUN chmod 0644 /etc/cron.d/hojo-collector
RUN touch /var/log/cron.log

# プロダクション用イメージ
FROM python:3.11-slim

WORKDIR /app

# システム依存関係のインストール（最小構成）
RUN apt-get update && apt-get install -y \
    postgresql-client \
    cron \
    && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/sbin/cron /usr/sbin/crond

# ビルド成果物をコピー
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# cronジョブの設定（既存の設定をコピー）
COPY --from=builder /etc/cron.d/hojo-collector /etc/cron.d/hojo-collector
COPY --from=builder /var/log/cron.log /var/log/cron.log

# 起動コマンド
CMD ["/usr/sbin/crond", "-f", "-l", "8"]
