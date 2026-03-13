# 補助金ポータルサイト 開発計画書

## 1. プロジェクト概要
- 目的: 日本のIT・ものづくり系補助金情報を集約するポータルサイトを提供する。
- 機能: 自動収集（J-Grants API、補助金ポータルスクレイピング）、一覧表示・検索・フィルタ、期限切れ表示制御、共有メモ、認証保護（Cloudflare Access）など。

## 2. システムアーキテクチャ
- コンポーネント:
  - **フロントエンド**: React (TypeScript) + Vite + Tailwind CSS
  - **バックエンド**: FastAPI (Python)
  - **データベース**: PostgreSQL
  - **データ収集サービス**: Pythonスクリプト（API取得、スクレイピング）
  - **定期実行**: cron (Docker内)
- 全体構成図（テキスト）: 
  - ユーザー → Cloudflare Access → フロントエンド → バックエンド → DB
  - 収集サービスはDBに直接書き込み

## 3. データソース
### 3.1 J-Grants API
- エンドポイント: `https://api.digital.go.jp/jgrants/v1/public/subsidies` (要確認)
- 認証: 現在の調査ではAPIキーが必要か不明（要確認）
- 取得項目: 必要に応じて全項目をマッピング

### 3.2 補助金ポータル (https://hojyokin-portal.jp/)
- スクレイピング: BeautifulSoup/Requests または Playwright を使用
- 対象ページ: 一覧ページおよび詳細ページ
- ポリシー: robots.txt を尊重、適切な間隔を空ける
- 取得項目: タイトル、説明、地域、実施機関、公募ステータス、申請期間、上限金額・助成額、補助率、目的、対象経費、対象事業者、公式公募ページURL、関連タグなど

## 4. データベース設計（案）
テーブル: `subsidies`
- `id` SERIAL PRIMARY KEY
- `source` VARCHAR (e.g., 'jgrants', 'portal')
- `external_id` VARCHAR (元サイトでのユニーク識別子)
- `title` TEXT
- `description` TEXT
- `region` TEXT
- `organization` TEXT
- `status` VARCHAR (公募ステータス)
- `start_date` DATE
- `end_date` DATE
- `amount` TEXT
- `subsidy_rate` TEXT
- `purpose` TEXT
- `eligible_expenses` TEXT
- `eligible_entities` TEXT
- `official_url` TEXT
- `tags` TEXT (JSON または 配列)
- `note` TEXT (共有メモ)
- `created_at` TIMESTAMP
- `updated_at` TIMESTAMP

※ 実際のフィールドは収集可能な項目に合わせて調整。

## 5. バックエンドAPI
基本認証: Cloudflare Accessにより保護されているため、アプリケーション内では追加認証は不要（ただし、必要に応じて簡易的なAPIキー認証も検討可能）。

エンドポイント:
- `GET /api/subsidies` – 補助金一覧（クエリパラメータによるフィルタ・ページネーション）
- `GET /api/subsidies/{id}` – 詳細情報
- `PUT /api/subsidies/{id}/note` – メモ更新（リクエストボディ: `{"note": "..."}`）

## 6. フロントエンド
### 6.1 ページ構成
- **一覧ページ**: カード形式の一覧、検索ボックス、フィルタサイドバー（地域、ステータス、期限切れ表示切り替え等）
- **詳細ページ**: 補助金の全項目表示、メモテキストエリア（自動保存、他ユーザー更新を定期的に取得）

### 6.2 メモ機能の動作
- テキストエリアの変更を検知し、デバウンス（例: 1秒後）で自動保存APIを呼び出す。
- 10秒ごとに最新のメモを取得し、テキストエリアの内容を更新（他ユーザーの変更を反映）。
- 競合解決は単純に上書き（最後の保存が優先）。

## 7. データ収集サービス
- 収集スクリプト: `collector.py`
  - J-Grants APIからデータ取得
  - 補助金ポータルからスクレイピング（詳細ページまでクロール）
  - 取得したデータをDBに保存（`external_id` による重複チェック）
- 定期実行: cronジョブで1日2回（9:00, 13:00）実行

## 8. 開発環境とDocker化
- 各サービスをDockerコンテナ化
- `docker-compose.yml` に以下を定義:
  - `db`: PostgreSQL
  - `backend`: FastAPI (ポート8000)
  - `frontend`: React ビルド成果物をサーブ（nginx または Vite 開発サーバー）
  - `collector`: Python + cron（定期実行）
- ボリューム: PostgreSQLデータ永続化

## 9. デプロイ
- 自社サーバーにDocker環境を構築
- Cloudflare Tunnel でサイトを公開
- Cloudflare Access を設定し、Google認証によるアクセス制限を適用
  - 設定手順は別ドキュメント `CLOUDFLARE_SETUP.md` に記載予定

## 10. 開発タスクリスト（順不同）
1. J-Grants APIの調査とテスト
2. 補助金ポータルのスクレイピング調査
3. データベース設計とマイグレーションスクリプト作成
4. バックエンドAPIの実装（一覧・詳細・メモ更新）
5. フロントエンドの実装（一覧・詳細・メモ機能）
6. データ収集サービスの実装
7. Docker構成の作成
8. 定期更新の設定
9. テスト（結合・動作確認）
10. デプロイ準備（ドキュメント作成、環境変数設定）

## 11. 未確定事項
- **J-Grants APIの認証**: APIキーの有無、取得方法を要確認
- **メモ機能の共有範囲**: 現在は全ユーザー共通と仮定。別の仕様が必要か？
- **APIキー認証についての要件**: バックエンドが外部システムから呼ばれる場合、APIキー認証が必要かどうか（現時点ではCloudflare Accessで保護）
- **初期データ投入**: 初回起動時に過去データを収集するバッチが必要か？

## 12. 今後の流れ
1. 本計画書をレビューいただき、未確定事項についてご指示ください。
2. ご承認後、Act Modeに切り替えて実装を開始します。