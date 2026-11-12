from datetime import datetime

from pydantic import BaseModel

from src.schemas.common import ORMModel, Timestamped


class ReviewDecisionRead(Timestamped):
    id: str
    anomaly_id: str
    fingerprint: str
    transaction_id: str
    decision: str
    reason: str
    version: int
    expected_version: int
    run_id: str
    analysis_id: str
    reviewer_id: str
    reviewer_name: str


class ReviewDecisionCreate(BaseModel):
    decision: str
    reason: str
    # 前端持有的当前版本号，用于乐观锁；不传则视为基于初始版本提交。
    expected_version: int = 0


class AnomalyRead(ORMModel):
    id: str
    fingerprint: str
    transaction_id: str
    merchant: str
    signal: dict
    rule_fingerprint: str
    data_checksum: str
    analysis_id: str
    workspace_id: str
    latest_run_id: str
    review_status: str
    version: int
    superseded: bool
    created_at: datetime
    updated_at: datetime


class AnomalyDetail(AnomalyRead):
    decisions: list[ReviewDecisionRead] = []


class AnomalyList(ORMModel):
    items: list[AnomalyRead]
    total: int
    summary: dict


class ConflictDetail(BaseModel):
    message: str
    current_version: int
    latest_decision: ReviewDecisionRead | None = None
