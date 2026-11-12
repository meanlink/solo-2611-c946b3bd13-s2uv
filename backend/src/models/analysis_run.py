from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.common import IdMixin, TimestampMixin


class AnalysisRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "analysis_runs"
    natural_key: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(24), default="draft")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[list] = mapped_column(JSON, default=list)
    error_message: Mapped[str] = mapped_column(Text, default="")
    checksum: Mapped[str] = mapped_column(String(64), default="")
    # 规则指纹：仅由检测规则（算法 config）决定，与数据指纹共同标识一次计算口径。
    rule_fingerprint: Mapped[str] = mapped_column(String(64), default="", index=True)
    # 本次运行幂等同步复核待办的统计（新建/复用/总数），便于审计重复运行行为。
    review_sync: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
