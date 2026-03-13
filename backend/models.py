from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Subsidy(Base):
    __tablename__ = "subsidies"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # 'jgrants' or 'portal'
    external_id = Column(String(255), nullable=False, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    region = Column(Text)
    organization = Column(Text)
    status = Column(String(100))  # e.g., '公募中', '終了'
    start_date = Column(Date)
    end_date = Column(Date)
    amount = Column(Text)  # 上限金額・助成額
    subsidy_rate = Column(Text)  # 補助率
    purpose = Column(Text)  # 目的
    eligible_expenses = Column(Text)  # 対象経費
    eligible_entities = Column(Text)  # 対象事業者
    official_url = Column(Text)
    tags = Column(JSONB)  # 関連タグを配列として保存
    note = Column(Text)  # 共有メモ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_source_external_id', 'source', 'external_id', unique=True),
    )