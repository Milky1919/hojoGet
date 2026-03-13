# 補助金ポータルサイト (hojo_get)

日本のIT・ものづくり系補助金情報を集約するポータルサイトです。J-Grants APIと補助金ポータルから自動収集し、検索・フィルタ機能を提供します。

## 機能

- **自動データ収集**: J-Grants APIと補助金ポータルから1日2回（9:00, 13:00）自動収集
- **補助金一覧**: カード形式での表示、検索・フィルタ機能
- **詳細表示**: 補助金の詳細情報（金額、対象、申請期間など）
- **共有メモ**: 各補助金にリアルタイム共有メモ機能
- **期限切れ管理**: 期限切れ補助金の視覚的区別とフィルタリング
- **レスポンシブデザイン**: モバイル対応

## 技術スタック

- **バックエンド**: Python FastAPI, PostgreSQL, SQLAlchemy
- **フロントエンド**: React (TypeScript), Vite, Tailwind CSS
- **データ収集**: Python (Requests, BeautifulSoup, Playwright)
- **コンテナ**: Docker, Docker Compose
- **定期実行**: cron

## ディレクトリ構成

```
hojo_get/
├── backend/           # FastAPIバックエンド
├── frontend/          # Reactフロントエンド
├── collector/         # データ収集サービス
├── docker-compose.yml # Docker Compose設定
├── PLAN.md           # プロジェクト計画書
└── README.md         # このファイル
```

## クイックスタート

### 1. 環境設定

```bash
# 環境変数ファイルの作成
cp .env.example .env

# .envファイルを編集（必要に応じて）
# DB_USER, DB_PASSWORD, API_KEYなどを設定
```

### 2. Dockerでの起動

```bash
# 全サービスを起動
docker-compose up -d

# 起動確認
docker-compose ps
```

### 3. サービスアクセス

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs

### 4. 初期データ投入

```bash
# 収集サービスの手動実行（コンテナ内）
docker-compose exec collector python collector.py
```

## 環境変数

`.env`ファイルで以下の変数を設定できます：

| 変数名 | 説明 | デフォルト |
|--------|------|------------|
| DB_USER | PostgreSQLユーザー名 | hojo_user |
| DB_PASSWORD | PostgreSQLパスワード | hojo_password |
| DB_NAME | データベース名 | hojo_db |
| API_KEY | バックエンドAPIキー | changeme |
| JGRANTS_API_KEY | J-Grants APIキー | （空） |
| VITE_API_BASE_URL | フロントエンドAPIベースURL | http://localhost:8000 |
| VITE_API_KEY | フロントエンドAPIキー | changeme |

## APIエンドポイント

### 補助金関連
- `GET /api/subsidies` - 補助金一覧（検索・フィルタ対応）
- `GET /api/subsidies/{id}` - 補助金詳細
- `PUT /api/subsidies/{id}/note` - メモ更新（APIキー必要）

### ヘルスチェック
- `GET /health` - サービス状態確認

## データ収集

収集サービスは以下のソースからデータを取得します：

1. **J-Grants API** (https://developers.digital.go.jp/documents/jgrants/api/)
   - APIキーが必要な場合があります
   - 定期的に全件取得

2. **補助金ポータル** (https://hojyokin-portal.jp/)
   - スクレイピングによる収集
   - robots.txtを尊重し、適切な間隔を空けてアクセス

収集頻度：1日2回（9:00, 13:00 JST）

## 開発

### バックエンド開発

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### フロントエンド開発

```bash
cd frontend
npm install
npm run dev
```

### データベースマイグレーション

```bash
# 初回セットアップ（テーブル作成）
docker-compose exec backend python -c "from main import Base, engine; Base.metadata.create_all(bind=engine)"
```

## デプロイ

### 自社サーバーでのデプロイ

1. DockerとDocker Composeをインストール
2. リポジトリをクローン
3. `.env`ファイルを設定
4. `docker-compose up -d`で起動

### Cloudflare Tunnelでの公開

1. Cloudflare Tunnelをセットアップ
2. トンネル設定でポート3000（フロントエンド）を公開
3. Cloudflare AccessでGoogle認証を設定（オプション）

## 注意事項

1. **スクレイピングの倫理**: 補助金ポータルのスクレイピングは、robots.txtを確認し、サーバー負荷を考慮して実装してください。
2. **API利用規約**: J-Grants APIの利用規約を確認し、遵守してください。
3. **データの正確性**: 収集したデータの正確性は保証されません。重要な判断には公式情報を参照してください。

## ライセンス

プロプライエタリ