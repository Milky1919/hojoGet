import os
import requests
import json
from datetime import datetime, date
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from bs4 import BeautifulSoup
import time
import pytz

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hojo_user:hojo_password@localhost:5432/hojo_db")
JGRANTS_API_KEY = os.getenv("JGRANTS_API_KEY", "")

# データベース接続
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class SubsidyCollector:
    def __init__(self):
        self.session = SessionLocal()
        self.jst = pytz.timezone('Asia/Tokyo')
    
    def collect_jgrants(self) -> List[Dict]:
        """J-Grants APIから補助金情報を収集"""
        logger.info("J-Grants APIからデータ収集を開始")
        
        # 注: 実際のAPIエンドポイントとパラメータは要確認
        # 仮のエンドポイントとレスポンス構造
        try:
            headers = {}
            if JGRANTS_API_KEY:
                headers["Authorization"] = f"Bearer {JGRANTS_API_KEY}"
            
            # 仮のAPI呼び出し（実際のAPI仕様に合わせて修正）
            response = requests.get(
                "https://api.digital.go.jp/jgrants/v1/public/subsidies",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                subsidies = data.get("subsidies", [])
                logger.info(f"J-Grantsから {len(subsidies)} 件の補助金を取得")
                return subsidies
            else:
                logger.error(f"J-Grants APIエラー: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"J-Grants収集エラー: {e}")
            return []
    
    def collect_portal(self) -> List[Dict]:
        """補助金ポータルからスクレイピング"""
        logger.info("補助金ポータルからデータ収集を開始")
        
        # 注: 実際のスクレイピングロジックは要実装
        # ここでは仮のデータを返す
        try:
            # 実際のスクレイピング例（コメントアウト）
            """
            url = "https://hojyokin-portal.jp/subsidies/list"
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 詳細ページへのリンクを抽出
            links = []
            for link in soup.select('a[href*="/subsidies/"]'):
                href = link.get('href')
                if href and 'list' not in href:
                    links.append(href)
            
            # 各詳細ページをクロール
            subsidies = []
            for link in links[:10]:  # 最初の10件のみ（テスト用）
                subsidy_data = self.scrape_detail_page(link)
                if subsidy_data:
                    subsidies.append(subsidy_data)
                time.sleep(1)  # サーバー負荷軽減
            """
            
            # 仮のデータ
            subsidies = [
                {
                    "external_id": "portal_001",
                    "title": "愛知県：中小企業デジタル化・DX促進補助金",
                    "description": "デジタル技術を活用し生産性向上に取り組む県内の中小企業・小規模企業者に対して、デジタルツール導入等の経費の一部を助成します。",
                    "region": "愛知県",
                    "organization": "公益財団法人あいち産業振興機構",
                    "status": "公募中",
                    "start_date": "2026-03-06",
                    "end_date": "2026-05-12",
                    "amount": "200万円",
                    "subsidy_rate": "・中小企業：1/2\n・小規模企業者：2/3",
                    "purpose": "設備投資／生産性向上・業務効率化／デジタル",
                    "eligible_expenses": "機械装置等費／委託費／外注費／借料／システム購入費/システム構築費／サービス利用料",
                    "eligible_entities": "中小企業／個人事業主／小規模事業者",
                    "official_url": "https://dx-hojo.aibsc.jp/",
                    "tags": ["設備投資", "生産性向上・業務効率化", "デジタル", "DX", "中小企業"]
                }
            ]
            
            logger.info(f"ポータルから {len(subsidies)} 件の補助金を取得")
            return subsidies
            
        except Exception as e:
            logger.error(f"ポータル収集エラー: {e}")
            return []
    
    def save_to_db(self, subsidies: List[Dict], source: str):
        """データベースに保存（重複チェック付き）"""
        logger.info(f"{source} のデータをDBに保存開始")
        
        for subsidy_data in subsidies:
            try:
                # 外部IDを生成
                external_id = subsidy_data.get("external_id", "")
                if not external_id:
                    # タイトルと地域からハッシュ生成
                    import hashlib
                    key = f"{subsidy_data.get('title', '')}_{subsidy_data.get('region', '')}"
                    external_id = hashlib.md5(key.encode()).hexdigest()
                
                # 既存データチェック
                query = text("""
                    SELECT id FROM subsidies 
                    WHERE source = :source AND external_id = :external_id
                """)
                result = self.session.execute(
                    query, 
                    {"source": source, "external_id": external_id}
                ).fetchone()
                
                if result:
                    # 更新
                    subsidy_id = result[0]
                    update_query = text("""
                        UPDATE subsidies SET
                            title = :title,
                            description = :description,
                            region = :region,
                            organization = :organization,
                            status = :status,
                            start_date = :start_date,
                            end_date = :end_date,
                            amount = :amount,
                            subsidy_rate = :subsidy_rate,
                            purpose = :purpose,
                            eligible_expenses = :eligible_expenses,
                            eligible_entities = :eligible_entities,
                            official_url = :official_url,
                            tags = :tags,
                            updated_at = NOW()
                        WHERE id = :id
                    """)
                    self.session.execute(update_query, {
                        **subsidy_data,
                        "id": subsidy_id,
                        "tags": json.dumps(subsidy_data.get("tags", []), ensure_ascii=False)
                    })
                    logger.debug(f"更新: {subsidy_data.get('title')}")
                else:
                    # 新規挿入
                    insert_query = text("""
                        INSERT INTO subsidies (
                            source, external_id, title, description, region,
                            organization, status, start_date, end_date, amount,
                            subsidy_rate, purpose, eligible_expenses, eligible_entities,
                            official_url, tags, created_at, updated_at
                        ) VALUES (
                            :source, :external_id, :title, :description, :region,
                            :organization, :status, :start_date, :end_date, :amount,
                            :subsidy_rate, :purpose, :eligible_expenses, :eligible_entities,
                            :official_url, :tags, NOW(), NOW()
                        )
                    """)
                    self.session.execute(insert_query, {
                        "source": source,
                        "external_id": external_id,
                        **subsidy_data,
                        "tags": json.dumps(subsidy_data.get("tags", []), ensure_ascii=False)
                    })
                    logger.debug(f"新規: {subsidy_data.get('title')}")
                    
            except Exception as e:
                logger.error(f"DB保存エラー: {e}")
                continue
        
        self.session.commit()
        logger.info(f"{source} のデータ保存完了")
    
    def run(self):
        """収集ジョブを実行"""
        logger.info("収集ジョブ開始")
        
        try:
            # J-Grants APIから収集
            jgrants_data = self.collect_jgrants()
            if jgrants_data:
                self.save_to_db(jgrants_data, "jgrants")
            
            # 補助金ポータルから収集
            portal_data = self.collect_portal()
            if portal_data:
                self.save_to_db(portal_data, "portal")
            
            logger.info("収集ジョブ完了")
            
        except Exception as e:
            logger.error(f"収集ジョブエラー: {e}")
        finally:
            self.session.close()

if __name__ == "__main__":
    collector = SubsidyCollector()
    collector.run()