from fastapi import FastAPI, Depends, HTTPException, Query, Header
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, func, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB
import os
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date
import pytz
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import Base, Subsidy

# 環境変数
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hojo_user:hojo_password@localhost:5432/hojo_db")
API_KEY = os.getenv("API_KEY", "changeme")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# データベース接続
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# テーブル作成（マイグレーションは別途Alembicで行うが、簡易的に）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="補助金ポータル API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydanticモデル
class SubsidyCreate(BaseModel):
    source: str
    external_id: str
    title: str
    description: Optional[str] = None
    region: Optional[str] = None
    prefecture: Optional[str] = None
    city: Optional[str] = None
    organization: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    amount: Optional[str] = None
    subsidy_rate: Optional[str] = None
    purpose: Optional[str] = None
    eligible_expenses: Optional[str] = None
    eligible_entities: Optional[str] = None
    official_url: Optional[str] = None
    tags: Optional[List[str]] = None

class SubsidyResponse(SubsidyCreate):
    id: int
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SubsidyUpdate(BaseModel):
    note: Optional[str] = None

# 依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# ヘルスチェック
@app.get("/health")
def health():
    return {"status": "ok"}

# グローバル例外ハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# 都道府県・市区町村一覧取得
@app.get("/api/regions")
def get_regions(db: Session = Depends(get_db)):
    rows = db.query(Subsidy.prefecture, Subsidy.city).filter(
        Subsidy.prefecture.isnot(None),
        Subsidy.prefecture != ""
    ).distinct().order_by(Subsidy.prefecture, Subsidy.city).all()

    result: dict = {}
    for row in rows:
        pref = row.prefecture or ""
        city = row.city or ""
        if not pref:
            continue
        if pref not in result:
            result[pref] = []
        if city and city not in result[pref]:
            result[pref].append(city)
    return result

# 補助金一覧取得
@app.get("/api/subsidies", response_model=List[SubsidyResponse])
def get_subsidies(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="検索キーワード"),
    region: Optional[str] = Query(None, description="地域（後方互換）"),
    prefecture: Optional[str] = Query(None, description="都道府県"),
    city: Optional[str] = Query(None, description="市区町村"),
    status: Optional[str] = Query(None, description="ステータス"),
    include_expired: bool = Query(False, description="期限切れを含む"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    query = db.query(Subsidy)

    # キーワード検索
    if q:
        query = query.filter(
            or_(
                Subsidy.title.ilike(f"%{q}%"),
                Subsidy.description.ilike(f"%{q}%"),
                Subsidy.region.ilike(f"%{q}%"),
            )
        )

    # フィルタ
    if prefecture:
        query = query.filter(Subsidy.prefecture == prefecture)
    if city:
        # city一致 OR city未設定（都道府県全体の補助金）も含める
        query = query.filter(
            (Subsidy.city == city) | (Subsidy.city == None) | (Subsidy.city == "")
        )
    if region:
        query = query.filter(Subsidy.prefecture.ilike(f"%{region}%"))
    if status:
        query = query.filter(Subsidy.status == status)
    
    # 期限切れ除外
    if not include_expired:
        today = datetime.now(pytz.UTC).date()
        query = query.filter(
            or_(
                Subsidy.end_date.is_(None),
                Subsidy.end_date >= today
            )
        )
    
    # ソート（終了日が近い順、新着順）
    query = query.order_by(
        Subsidy.end_date.asc().nulls_last(),
        Subsidy.created_at.desc()
    )
    
    subsidies = query.offset(offset).limit(limit).all()
    return subsidies

# 補助金詳細取得
@app.get("/api/subsidies/{subsidy_id}", response_model=SubsidyResponse)
def get_subsidy(subsidy_id: int, db: Session = Depends(get_db)):
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")
    return subsidy

# メモ更新
@app.put("/api/subsidies/{subsidy_id}/note")
def update_note(
    subsidy_id: int,
    data: SubsidyUpdate,
    db: Session = Depends(get_db),
    api_key: bool = Depends(verify_api_key),
):
    subsidy = db.query(Subsidy).filter(Subsidy.id == subsidy_id).first()
    if not subsidy:
        raise HTTPException(status_code=404, detail="Subsidy not found")
    
    subsidy.note = data.note
    db.commit()
    db.refresh(subsidy)
    return {"message": "Note updated", "note": subsidy.note}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)