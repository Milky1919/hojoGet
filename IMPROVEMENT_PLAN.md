# 改善作業プラン

このドキュメントは、ActモードでAIが作業するための詳細な手順書です。

---

## 作業1: Dockerビルド問題の修正（優先度：高）

### 問題
collectorサービスのDockerビルド時にPlaywrightのインストールでネットワークタイムアウトが発生

### 修正手順

#### ステップ1: collector/requirements.txtの編集
```
ファイル: collector/requirements.txt

現在の内容:
requests==2.31.0
beautifulsoup4==4.12.2
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
playwright==1.40.0
pytz==2023.3
schedule==1.2.0

↓ 変更後:

requests==2.31.0
beautifulsoup4==4.12.2
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
pytz==2023.3
schedule==1.2.0
```

#### ステップ2: collector/Dockerfileの編集
```
ファイル: collector/Dockerfile

削除する行:
RUN pip install playwright && playwright install chromium

※ playwright関連の行をすべて削除すること
```

#### ステップ3: Dockerビルドの実行
```bash
docker-compose build --no-cache collector
```

#### ステップ4: 動作確認
```bash
docker-compose up -d collector
docker-compose logs collector
```

---

## 作業2: J-Grants APIの実装（優先度：中）

### 事前調査（Actモードに入る前に実施）
以下の作業をブラウザで実施してください：

1. 以下のURLにアクセス:
   https://developers.digital.go.jp/documents/jgrants/api/

2. 以下の項目を確認:
   - APIエンドポイント（URL）
   - 認証方法（APIキーが必要か）
   - レスポンスのデータ構造（JSONの形式）

3. 確認結果をメモする

### 実装手順

#### ステップ1: 環境変数の設定
```
.envファイルに以下を追加:
JGRANTS_API_KEY=（取得したAPIキー）
```

#### ステップ2: collector/collector.pyの編集

以下の関数を修正:

```python
def collect_jgrants(self) -> List[Dict]:
    """J-Grants APIから補助金情報を収集"""
    logger.info("J-Grants APIからデータ収集を開始")
    
    # TODO: 事前調査で得た正しいエンドポイントに書き換える
    api_url = "事前調査で確認したURL"
    
    headers = {}
    api_key = os.getenv("JGRANTS_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # TODO: レスポンスのJSON構造に合わせて書き換える
            subsidies = data.get("subsidies", [])
            logger.info(f"J-Grantsから {len(subsidies)} 件の補助金を取得")
            return subsidies
        else:
            logger.error(f"J-Grants APIエラー: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"J-Grants収集エラー: {e}")
        return []
```

#### ステップ3: テスト実行
```bash
# コンテナ内で直接実行
docker-compose exec collector python collector.py

# ログ確認
docker-compose logs collector
```

---

## 作業3: 補助金ポータル スクレイピングの実装（優先度：中）

### 事前調査（Actモードに入る前に実施）

1. ブラウザで以下URLにアクセス:
   https://hojyokin-portal.jp/subsidies/list

2. Chrome DevTools（F12）で以下を確認:
   - 補助金一覧のHTML構造
   - 各補助金カードの詳細情報のHTMLクラス名
   - 詳細ページへのリンクURLパターン

3. 確認結果をメモする

### 実装手順

#### ステップ1: collector/collector.pyの編集

```python
def collect_portal(self) -> List[Dict]:
    """補助金ポータルからスクレイピング"""
    logger.info("補助金ポータルからデータ収集を開始")
    
    subsidies = []
    
    try:
        # 一覧ページの取得
        url = "https://hojyokin-portal.jp/subsidies/list"
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TODO: 事前調査で確認したHTML構造に合わせて書き換える
        # 例：すべての補助金カードを抽出
        items = soup.select('.subsidy-card')  # 適切なCSS selectorに書き換え
        
        for item in items[:10]:  # 最初の10件のみ（テスト用）
            try:
                # タイトル
                title = item.select_one('.title').text.strip()
                
                # 詳細ページURL
                detail_url = item.select_one('a[href*="/subsidies/"]').get('href')
                
                # 詳細ページから情報を取得
                detail_response = requests.get(detail_url, timeout=30)
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                
                # 必要な情報を抽出（HTML構造に合わせて書き換え）
                subsidy_data = {
                    "title": title,
                    "description": detail_soup.select_one('.description').text.strip(),
                    "region": detail_soup.select_one('.region').text.strip(),
                    "amount": detail_soup.select_one('.amount').text.strip(),
                    "end_date": detail_soup.select_one('.deadline').text.strip(),
                    "official_url": detail_url,
                }
                
                subsidies.append(subsidy_data)
                
                # サーバー負荷軽減
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"詳細ページ取得エラー: {e}")
                continue
        
        logger.info(f"ポータルから {len(subsidies)} 件の補助金を取得")
        return subsidies
        
    except Exception as e:
        logger.error(f"ポータル収集エラー: {e}")
        return []
```

#### ステップ2: テスト実行
```bash
docker-compose exec collector python collector.py
docker-compose logs collector
```

---

## 作業4: システム全体の動作確認（優先度：高）

### 4.1 全サービスの起動確認

```bash
# すべてのサービスが起動しているか確認
docker-compose ps

# 各サービスの状態を確認
docker-compose logs --tail=10 backend
docker-compose logs --tail=10 frontend
docker-compose logs --tail=10 db
docker-compose logs --tail=10 collector
```

### 4.2 バックエンドAPIテスト

```bash
# ヘルスチェック
curl http://localhost:8000/health

# 補助金一覧API
curl "http://localhost:8000/api/subsidies?limit=5"

# 詳細API（ID=1の補助金）
curl http://localhost:8000/api/subsidies/1
```

### 4.3 データベース接続確認

```bash
# データベースコンテナ内で接続テスト
docker-compose exec db psql -U hojo_user -d hojo_db -c "SELECT COUNT(*) FROM subsidies;"

# テーブル構造確認
docker-compose exec db psql -U hojo_user -d hojo_db -c "\d subsidies"
```

### 4.4 フロントエンド動作確認

```bash
# フロントエンドのビルドと起動
docker-compose build frontend
docker-compose up -d frontend
```

#### ブラウザで確認
```
URL: http://localhost:3000
```

#### 動作確認項目
- [ ] 補助金一覧ページが表示される
- [ ] キーワード検索が機能する
- [ ] 地域フィルタが機能する
- [ ] 詳細ページへのリンクが機能する
- [ ] 詳細ページでメモの編集ができる

### 4.5 collectorサービス動作確認

```bash
# collectorの手動実行
docker-compose exec collector python collector.py

# ログ確認
docker-compose logs collector

# 収集したデータの確認
docker-compose exec db psql -U hojo_user -d hojo_db -c "SELECT title, source FROM subsidies ORDER BY created_at DESC LIMIT 5;"
```

### 4.6 統合テスト

1. **フロントエンド ↔ バックエンド連携**
   - ブラウザで http://localhost:3000 にアクセス
   - 補助金一覧が表示されることを確認
   - 検索機能が動作することを確認

2. **collector → データベース連携**
   - collectorがデータを収集してDBに保存
   - フロントエンドで収集したデータが表示される

3. **定期実行の確認**
   - collectorの定期実行が設定されているか確認
   - cronジョブが正しく動作しているか確認

---

## 緊急時の対応

### Dockerビルドが失敗する場合
```bash
# キャッシュをクリアして再ビルド
docker-compose build --no-cache サービス名
```

### データベース接続エラー
```bash
# DBの状態を確認
docker-compose logs db

# DBの再起動
docker-compose restart db
```

### バックエンドが起動しない場合
```bash
# ログを確認
docker-compose logs backend

# 完全再起動
docker-compose restart backend
```
