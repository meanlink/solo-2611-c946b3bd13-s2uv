from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.common import IdMixin, TimestampMixin


class ReviewDecision(IdMixin, TimestampMixin, Base):
    """逐笔复核结论的不可变历史记录（append-only）。

    每次判定都新增一行而非覆盖：理由、判定人、判定时间以及当时的版本
    全部留痕，即使源数据或规则更新后重新复核，旧结论依旧可以追溯。
    anomaly_transaction 的最新状态由 version 最大的一行决定。
    """

    __tablename__ = "review_decisions"
    anomaly_id: Mapped[str] = mapped_column(String(36), index=True)
    # 冗余指纹，便于在待办被新一代结果取代后仍能按交易回溯历史结论。
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    transaction_id: Mapped[str] = mapped_column(String(96), index=True)
    decision: Mapped[str] = mapped_column(String(24), index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    expected_version: Mapped[int] = mapped_column(Integer, default=0)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), index=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), index=True)
    reviewer_name: Mapped[str] = mapped_column(String(120), default="")
