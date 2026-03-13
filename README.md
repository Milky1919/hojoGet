# 補助金ポータル (hojoGet)

IT・ものづくり系の補助金情報を収集・表示するWebアプリケーションです。

## 機能

- **補助金一覧表示**: 地域、キーワード、ステータスでのフィルタリング
- **詳細表示**: 各補助金の詳細情報と共有メモ機能
- **自動収集**: J-Grants APIとポータルサイトからの定期的なデータ収集
- **リアルタイム更新**: メモの自動保存と共有

## 技術スタック

- **バックエンド**: FastAPI (Python), PostgreSQL, SQLAlchemy
- **フロントエンド**: React (TypeScript), Vite, Tailwind CSS
- **データ収集**: Pythonスクレイピング + cron定期実行
- **コンテナ化**: Docker Compose
- **デプロイ**: Dockge対応

## クイックスタート

### 前提条件

- Docker と Docker Compose
- Git

### 環境設定

1. リポジトリをクローン:
   ```bash
   git clone https://github.com/Milky1919/hojoGet.git
   cd hojoGet
   ```

2. 環境変数ファイルを作成:
   ```bash
   cp .env.example .env
   # .envファイルを編集（必要に応じて）
   ```

### Docker Composeでの起動

```bash
docker-compose up -d
```

または

```bash
docker compose up -d
```

### Dockgeでのデプロイ

1. Dockgeをインストール済みのサーバーで、このリポジトリをクローン
2. DockgeのWeb UIから「スタックの追加」を選択
3. 以下の設定でスタックを作成:
   - **スタック名**: `hojo-get`
   - **スタックファイルのパス**: `/path/to/hojoGet/compose.yaml`
   - **環境変数ファイル**: `/path/to/hojoGet/.env`（オプション）

4. 「デプロイ」をクリック

## サービス構成

| サービス | ポート | 説明 |
|----------|--------|------|
| frontend | 3000 | Reactフロントエンド |
| backend  | 8000 | FastAPIバックエンド |
| db       | 5432 | PostgreSQLデータベース |
| collector | - | データ収集サービス |

## 環境変数

`.env`ファイルで設定可能な環境変数:

```env
# データベース設定
DB_USER=hojo_user
DB_PASSWORD=hojo_password
DB_NAME=hojo_db

# API設定
API_KEY=changeme  # メモ更新用APIキー
JGRANTS_API_KEY=  # J-Grants APIキー（オプション）

# フロントエンド設定
VITE_API_BASE_URL=http://localhost:8000
```

## 開発

### バックエンド開発

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### フロントエンド開発

```bash
cd frontend
npm install
npm run dev
```

### データ収集のテスト

```bash
docker-compose exec collector python collector.py
```

## プロジェクト構造

```
hojoGet/
├── backend/           # FastAPIバックエンド
│   ├── main.py       # APIエンドポイント
│   ├── models.py     # データベースモデル
│   └── requirements.txt
├── frontend/         # Reactフロントエンド
│   ├── src/
│   │   ├── pages/    # ページコンポーネント
│   │   └── App.tsx   # メインアプリ
│   └── package.json
├── collector/        # データ収集サービス
│   └── collector.py  # 収集スクリプト
├── compose.yaml      # Dockge対応Composeファイル
├── docker-compose.yml # 従来のComposeファイル
└── .env.example      # 環境変数テンプレート
```

## ライセンス

MIT