FROM python:3.11-slim

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

# 起動コマンド
CMD ["/usr/sbin/crond", "-f", "-l", "8"]