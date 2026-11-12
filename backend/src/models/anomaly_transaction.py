from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.common import IdMixin, TimestampMixin


class AnomalyTransaction(IdMixin, TimestampMixin, Base):
    """一次检测命中的单笔异常交易，即一条复核待办。

    自然指纹由「分析方案 + 规则指纹 + 源数据指纹 + 交易主键」构成：
    同一份数据按相同规则重复运行时指纹不变，因此复用同一条待办，
    已有的复核结论继续沿用；源数据或规则变化后指纹变化，会产生新待办，
    需要重新复核，而历史结论仍保留在 review_decisions 中可追溯。
    """

    __tablename__ = "anomaly_transactions"
    natural_key: Mapped[str] = mapped_column(String(220), unique=True, index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    transaction_id: Mapped[str] = mapped_column(String(96), index=True)
    merchant: Mapped[str] = mapped_column(String(160), default="")
    signal: Mapped[dict] = mapped_column(JSON, default=dict)
    rule_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    data_checksum: Mapped[str] = mapped_column(String(64), default="")
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    workspace_id: Mapped[str] = mapped_column(String(36), index=True)
    latest_run_id: Mapped[str] = mapped_column(String(36), index=True)
    review_status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    # 当前结论的乐观锁版本：每次新增判定 +1，并发提交用它检测冲突。
    version: Mapped[int] = mapped_column(Integer, default=0)
    superseded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
