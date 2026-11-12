from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.schemas.review import (
    AnomalyDetail,
    AnomalyList,
    AnomalyRead,
    ReviewDecisionCreate,
    ReviewDecisionRead,
)
from src.services import audit_service, review_service


def list_items(db: Session, analysis_id: str | None, review_status: str | None,
               include_superseded: bool, merchant: str | None) -> AnomalyList:
    items = review_service.list_anomalies(
        db, analysis_id=analysis_id, review_status=review_status,
        include_superseded=include_superseded, merchant=merchant,
    )
    summary = review_service.review_summary(db, analysis_id)
    return AnomalyList(
        items=[AnomalyRead.model_validate(item) for item in items],
        total=len(items),
        summary=summary,
    )


def get_item(db: Session, anomaly_id: str) -> AnomalyDetail:
    anomaly = review_service.get_anomaly(db, anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="异常交易不存在")
    payload = AnomalyDetail.model_validate(anomaly)
    payload.decisions = [
        ReviewDecisionRead.model_validate(item)
        for item in review_service.list_decisions(db, anomaly_id)
    ]
    return payload


def decide(db: Session, anomaly_id: str, payload: ReviewDecisionCreate, user) -> ReviewDecisionRead:
    anomaly = review_service.get_anomaly(db, anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="异常交易不存在")
    if anomaly.superseded:
        raise HTTPException(
            status_code=409,
            detail="该待办已被新一代检测结果取代，请在最新待办上复核；历史结论仍可追溯。",
        )
    record = review_service.submit_decision(
        db, anomaly,
        decision=payload.decision,
        reason=payload.reason,
        expected_version=payload.expected_version,
        user=user,
        run_id=anomaly.latest_run_id,
    )
    audit_service.record(
        db, "review.decide", "anomaly_transaction", anomaly_id, user.id,
        {"decision": payload.decision, "version": record.version,
         "transaction_id": anomaly.transaction_id, "analysis_id": anomaly.analysis_id},
    )
    db.commit()
    db.refresh(record)
    return ReviewDecisionRead.model_validate(record)


def history(db: Session, transaction_id: str) -> list[ReviewDecisionRead]:
    records = review_service.list_decisions_by_transaction(db, transaction_id)
    return [ReviewDecisionRead.model_validate(item) for item in records]
