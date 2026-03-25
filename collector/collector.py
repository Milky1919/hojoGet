import os
import requests
import json
import re
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

# データベース接続
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# J-Grants API設定
JGRANTS_API_BASE = "https://api.jgrants-portal.go.jp/exp/v1/public"

# IT・ものづくり系のキーワード一覧
JGRANTS_KEYWORDS = [
    "IT", "DX", "デジタル", "ものづくり", "システム",
    "ソフトウェア", "情報通信", "IoT", "AI", "クラウド",
    "セキュリティ", "ロボット", "自動化", "省力化", "設備投資",
    "生産性向上", "スタートアップ", "創業", "研究開発", "EV",
    "省エネ", "再生可能エネルギー", "カーボンニュートラル", "GX",
    "EC", "販路開拓", "海外展開", "輸出", "人材育成", "雇用",
]

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]


def parse_region(text: str):
    """地域テキストから(都道府県, 市区町村)を抽出して返す"""
    if not text:
        return "", ""
    text = text.strip()
    if text == "全国":
        return "全国", ""

    prefecture = ""
    pos = -1
    for pref in PREFECTURES:
        idx = text.find(pref)
        if idx >= 0 and (pos < 0 or idx < pos):
            prefecture = pref
            pos = idx

    if not prefecture:
        return "", ""

    rest = text[pos + len(prefecture):]
    city_match = re.match(r'^([^\s、，,。・/／\n]{1,20}?[市区町村郡])', rest)
    city = city_match.group(1) if city_match else ""
    return prefecture, city


def extract_city_from_title(title: str) -> str:
    """タイトルから市区町村を抽出する（prefectureが既知の場合の補完用）
    対応パターン:
      - 「知立市カーボン...」 → 知立市
      - 「【東海市】東海市...」 → 東海市
      - 「神奈川県横浜市：...」 → 横浜市（parse_regionで取れるので補助的）
    """
    if not title:
        return ""
    # 【市区町村】パターン
    m = re.search(r'[【\[]([^\]】]{1,15}[市区町村郡])[】\]]', title)
    if m:
        return m.group(1)
    # 先頭が市区町村名で始まるパターン（都道府県なし）
    m = re.match(r'^([^\s【】「」（）：:\n]{1,15}[市区町村郡])', title)
    if m:
        candidate = m.group(1)
        # 都道府県名そのものは除外
        if candidate not in PREFECTURES:
            return candidate
    return ""


def strip_html(html_text: str) -> str:
    """HTMLタグを除去してテキストを返す"""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator='\n').strip()


def parse_jgrants_date(dt_str: Optional[str]) -> Optional[str]:
    """J-Grants APIの日時文字列をYYYY-MM-DD形式に変換"""
    if not dt_str:
        return None
    try:
        # "2026-03-13T01:00:00.000Z" または "2026-03-13T01:00Z" 形式
        dt_str = re.sub(r'\.\d+Z$', 'Z', dt_str)
        dt_str = dt_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt_str)
        jst = pytz.timezone('Asia/Tokyo')
        dt_jst = dt.astimezone(jst)
        return dt_jst.strftime('%Y-%m-%d')
    except Exception:
        return None


class SubsidyCollector:
    def __init__(self):
        self.session = SessionLocal()
        self.jst = pytz.timezone('Asia/Tokyo')

    def collect_jgrants(self) -> List[Dict]:
        """J-Grants APIから補助金情報を収集"""
        logger.info("J-Grants APIからデータ収集を開始")

        collected_ids = set()
        subsidies = []

        for keyword in JGRANTS_KEYWORDS:
            try:
                offset = 0
                limit = 100
                while True:
                    params = {
                        "keyword": keyword,
                        "sort": "acceptance_end_datetime",
                        "order": "ASC",
                        "acceptance": "1",
                        "limit": limit,
                        "offset": offset,
                    }
                    response = requests.get(
                        f"{JGRANTS_API_BASE}/subsidies",
                        params=params,
                        timeout=30
                    )

                    if response.status_code != 200:
                        logger.warning(f"J-Grants API エラー (keyword={keyword}): {response.status_code}")
                        break

                    data = response.json()
                    results = data.get("result", [])
                    if offset == 0:
                        logger.info(f"keyword='{keyword}' で {len(results)} 件取得")

                    new_count = 0
                    for item in results:
                        item_id = item.get("id")
                        if not item_id or item_id in collected_ids:
                            continue
                        collected_ids.add(item_id)
                        detail = self.fetch_jgrants_detail(item_id)
                        if detail:
                            subsidies.append(detail)
                        new_count += 1
                        time.sleep(0.3)

                    # 取得件数がlimitより少なければ最終ページ
                    if len(results) < limit:
                        break
                    offset += limit

            except Exception as e:
                logger.error(f"J-Grants収集エラー (keyword={keyword}): {e}")
                continue

        logger.info(f"J-Grantsから合計 {len(subsidies)} 件の補助金を取得")
        return subsidies

    def fetch_jgrants_detail(self, subsidy_id: str) -> Optional[Dict]:
        """J-Grants APIから補助金詳細を取得してDBスキーマに合わせて変換"""
        try:
            response = requests.get(
                f"{JGRANTS_API_BASE}/subsidies/id/{subsidy_id}",
                timeout=30
            )
            if response.status_code != 200:
                return None

            results = response.json().get("result", [])
            if not results:
                return None

            item = results[0]

            # 上限金額をテキスト形式に変換
            max_limit = item.get("subsidy_max_limit", 0)
            if max_limit and max_limit > 0:
                amount = f"{max_limit:,}円"
            else:
                amount = "上限なし / 要確認"

            title = item.get("title", "")
            pref, city_val = parse_region(item.get("target_area_search", "全国"))
            if not city_val:
                city_val = extract_city_from_title(title)
            return {
                "external_id": item.get("id"),
                "title": title,
                "description": strip_html(item.get("detail", "")),
                "region": item.get("target_area_search", "全国"),
                "prefecture": pref,
                "city": city_val,
                "organization": item.get("industry", ""),
                "status": "公募中",
                "start_date": parse_jgrants_date(item.get("acceptance_start_datetime")),
                "end_date": parse_jgrants_date(item.get("acceptance_end_datetime")),
                "amount": amount,
                "subsidy_rate": item.get("subsidy_rate") or "",
                "purpose": item.get("use_purpose", ""),
                "eligible_expenses": "",
                "eligible_entities": item.get("target_number_of_employees", ""),
                "official_url": item.get("front_subsidy_detail_page_url", ""),
                "tags": [item.get("industry", ""), item.get("use_purpose", "")],
            }

        except Exception as e:
            logger.error(f"J-Grants詳細取得エラー (id={subsidy_id}): {e}")
            return None

    def collect_portal(self, max_pages: int = 15) -> List[Dict]:
        """補助金ポータルからスクレイピング（最新ページをmax_pages分取得）"""
        logger.info("補助金ポータルからデータ収集を開始")

        subsidies = []
        base_url = "https://hojyokin-portal.jp"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        collected_urls = set()

        try:
            for page in range(1, max_pages + 1):
                try:
                    list_url = f"{base_url}/subsidies/list?page={page}"
                    response = requests.get(list_url, headers=headers, timeout=30)
                    if response.status_code != 200:
                        logger.warning(f"ポータル一覧取得エラー page={page}: {response.status_code}")
                        break

                    soup = BeautifulSoup(response.text, 'html.parser')

                    links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if '/subsidies/' in href and 'list' not in href and 'search' not in href:
                            if href.startswith('/'):
                                href = base_url + href
                            if href.startswith(base_url) and href not in collected_urls:
                                links.append(href)
                                collected_urls.add(href)

                    if not links:
                        logger.info(f"page={page} でリンクなし、終了")
                        break

                    logger.info(f"page={page}: {len(links)} 件のリンクを検出")
                    time.sleep(1)

                    for link in links:
                        try:
                            detail = self.scrape_portal_detail(link, headers)
                            if detail:
                                subsidies.append(detail)
                            time.sleep(1)
                        except Exception as e:
                            logger.error(f"ポータル詳細取得エラー ({link}): {e}")

                except Exception as e:
                    logger.error(f"ポータル収集エラー page={page}: {e}")
                    break

        except Exception as e:
            logger.error(f"ポータル収集エラー: {e}")

        logger.info(f"ポータルから {len(subsidies)} 件の補助金を取得")
        return subsidies

    def scrape_portal_detail(self, url: str, headers: dict) -> Optional[Dict]:
        """補助金ポータルの詳細ページをスクレイピング"""
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # タイトル
            title_el = soup.find('h1') or soup.find('h2')
            if not title_el:
                return None
            title = title_el.get_text(strip=True)
            if not title:
                return None

            # external_id: URLの末尾部分
            external_id = url.rstrip('/').split('/')[-1]

            # ページのテキストから各フィールドを抽出するヘルパー
            def find_field(labels: List[str]) -> str:
                for label in labels:
                    el = soup.find(string=re.compile(label))
                    if el:
                        parent = el.parent
                        # 隣接するdd/td/span要素を探す
                        sibling = parent.find_next_sibling()
                        if sibling:
                            return sibling.get_text(strip=True)
                        # 親の次の要素
                        if parent.parent:
                            next_el = parent.parent.find_next_sibling()
                            if next_el:
                                return next_el.get_text(strip=True)
                return ""

            # 説明文
            description = ""
            for tag in ['p', 'div']:
                els = soup.find_all(tag)
                for el in els:
                    text = el.get_text(strip=True)
                    if len(text) > 50:
                        description = text[:500]
                        break
                if description:
                    break

            region_text = find_field(['対象地域', '地域', '所在地'])
            pref, city_val = parse_region(region_text)
            # region_textから取れなければタイトル先頭から抽出
            if not pref:
                pref, city_val = parse_region(title)
            return {
                "external_id": f"portal_{external_id}",
                "title": title,
                "description": description,
                "region": region_text,
                "prefecture": pref,
                "city": city_val,
                "organization": find_field(['実施機関', '主催', '運営']),
                "status": "公募中",
                "start_date": None,
                "end_date": None,
                "amount": find_field(['上限金額', '補助金額', '助成額', '支援額']),
                "subsidy_rate": find_field(['補助率', '助成率']),
                "purpose": find_field(['目的', '活用目的']),
                "eligible_expenses": find_field(['対象経費', '補助対象経費']),
                "eligible_entities": find_field(['対象事業者', '対象者', '申請対象']),
                "official_url": url,
                "tags": [],
            }

        except Exception as e:
            logger.error(f"ポータル詳細スクレイピングエラー: {e}")
            return None

    def save_to_db(self, subsidies: List[Dict], source: str):
        """データベースに保存（重複チェック付き）"""
        logger.info(f"{source} のデータをDBに保存開始")

        for subsidy_data in subsidies:
            try:
                external_id = subsidy_data.get("external_id", "")
                if not external_id:
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
                    subsidy_id = result[0]
                    update_query = text("""
                        UPDATE subsidies SET
                            title = :title,
                            description = :description,
                            region = :region,
                            prefecture = :prefecture,
                            city = :city,
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
                    insert_query = text("""
                        INSERT INTO subsidies (
                            source, external_id, title, description, region,
                            prefecture, city,
                            organization, status, start_date, end_date, amount,
                            subsidy_rate, purpose, eligible_expenses, eligible_entities,
                            official_url, tags, created_at, updated_at
                        ) VALUES (
                            :source, :external_id, :title, :description, :region,
                            :prefecture, :city,
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
                self.session.rollback()
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
