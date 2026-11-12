import hashlib
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants.enums import REVIEW_DECISIONS, ReviewStatus
from src.models.analysis import Analysis
from src.models.anomaly_transaction import AnomalyTransaction
from src.models.review_decision import ReviewDecision
from src.services.errors import ReviewConflictError


def rule_fingerprint(config: dict) -> str:
    """规则指纹：仅由检测规则参数决定。规则更新后该指纹随之变化。"""
    canonical = json.dumps(config or {}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(("rule:" + canonical).encode()).hexdigest()


def anomaly_fingerprint(analysis_id: str, rule_fp: str, data_checksum: str,
                        transaction_id: str) -> str:
    """单笔异常的稳定指纹：方案 + 规则 + 数据 + 交易主键。

    同一份数据按相同规则重复运行时四项均不变，指纹一致，从而复用待办；
    源数据 checksum 或规则 config 任一变化都会得到新指纹，触发重新复核。
    """
    raw = "|".join([analysis_id, rule_fp, data_checksum, str(transaction_id)])
    return hashlib.sha256(raw.encode()).hexdigest()


def sync_anomalies(db: Session, run, analysis: Analysis) -> dict:
    """根据一次运行的命中结果幂等同步复核待办。

    - 指纹已存在：不重复建待办，只把 latest_run_id 指向本次运行，沿用已有结论。
    - 新指纹（新交易 / 数据更新 / 规则更新）：新建 pending 待办。
    - 同一方案下、本次规则+数据口径之外的历史待办标记 superseded，
      它们的结论仍保留在 review_decisions 中可追溯，不再出现在默认待办列表。
    """
    result = run.result or {}
    flagged = result.get("flagged") or []
    rule_fp = run.rule_fingerprint or rule_fingerprint(analysis.config or {})
    data_checksum = run.checksum or ""

    created = reused = 0
    current_fingerprints: set[str] = set()
    for item in flagged:
        txn_id = str(item.get("transaction_id", ""))
        fp = anomaly_fingerprint(analysis.id, rule_fp, data_checksum, txn_id)
        current_fingerprints.add(fp)
        existing = db.scalar(
            select(AnomalyTransaction).where(AnomalyTransaction.fingerprint == fp)
        )
        if existing:
            existing.latest_run_id = run.id
            existing.superseded = False
            reused += 1
            continue
        db.add(AnomalyTransaction(
            natural_key=fp,
            fingerprint=fp,
            transaction_id=txn_id,
            merchant=str(item.get("merchant", "")),
            signal={k: v for k, v in item.items() if k != "transaction_id"},
            rule_fingerprint=rule_fp,
            data_checksum=data_checksum,
            analysis_id=analysis.id,
            workspace_id=analysis.workspace_id,
            latest_run_id=run.id,
            review_status=ReviewStatus.PENDING.value,
            version=0,
            superseded=False,
        ))
        created += 1

    if current_fingerprints:
        stale = db.scalars(
            select(AnomalyTransaction).where(
                AnomalyTransaction.analysis_id == analysis.id,
                AnomalyTransaction.superseded.is_(False),
                AnomalyTransaction.fingerprint.notin_(current_fingerprints),
            )
        )
        for old in stale:
            old.superseded = True

    db.flush()
    return {"created": created, "reused": reused, "total": len(current_fingerprints)}


def list_anomalies(db: Session, *, analysis_id: str | None = None,
                   review_status: str | None = None, include_superseded: bool = False,
                   merchant: str | None = None) -> list[AnomalyTransaction]:
    stmt = select(AnomalyTransaction)
    if not include_superseded:
        stmt = stmt.where(AnomalyTransaction.superseded.is_(False))
    if analysis_id:
        stmt = stmt.where(AnomalyTransaction.analysis_id == analysis_id)
    if review_status:
        stmt = stmt.where(AnomalyTransaction.review_status == review_status)
    if merchant:
        stmt = stmt.where(AnomalyTransaction.merchant.ilike(f"%{merchant}%"))
    stmt = stmt.order_by(AnomalyTransaction.review_status,
                         AnomalyTransaction.created_at.desc())
    return list(db.scalars(stmt))


def get_anomaly(db: Session, anomaly_id: str) -> AnomalyTransaction | None:
    return db.get(AnomalyTransaction, anomaly_id)


def list_decisions(db: Session, anomaly_id: str) -> list[ReviewDecision]:
    """按版本正序返回一笔交易的全部历史结论（旧结论可追溯）。"""
    return list(db.scalars(
        select(ReviewDecision)
        .where(ReviewDecision.anomaly_id == anomaly_id)
        .order_by(ReviewDecision.version.asc(), ReviewDecision.created_at.asc())
    ))


def list_decisions_by_transaction(db: Session, transaction_id: str) -> list[ReviewDecision]:
    """跨代（数据/规则更新前后）按交易主键回溯全部历史结论。"""
    return list(db.scalars(
        select(ReviewDecision)
        .where(ReviewDecision.transaction_id == transaction_id)
        .order_by(ReviewDecision.created_at.desc())
    ))


def submit_decision(db: Session, anomaly: AnomalyTransaction, *, decision: str,
                    reason: str, expected_version: int, user,
                    run_id: str) -> ReviewDecision:
    """提交逐笔判定，带乐观锁冲突检测。

    两人同时提交同一笔交易时：先提交者把 version 从 N 推进到 N+1；
    后提交者仍基于 N 提交，expected_version 与当前 version 不符 → 409，
    响应体带回最新结论，前端据此提示冲突而不是覆盖前人判断。
    """
    if decision not in REVIEW_DECISIONS:
        raise HTTPException(status_code=400, detail="判定结果只能是误报或待追查")
    reason = (reason or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="请填写复核理由")

    # 行级条件更新实现乐观锁：只有版本匹配时才推进，避免并发覆盖。
    current_version = anomaly.version
    if expected_version != current_version:
        latest = db.scalar(
            select(ReviewDecision)
            .where(ReviewDecision.anomaly_id == anomaly.id)
            .order_by(ReviewDecision.version.desc())
        )
        raise ReviewConflictError(
            message="该交易已被其他复核员更新，提交存在冲突，请基于最新结论重新判定。",
            current_version=current_version,
            latest_decision=_decision_payload(latest),
        )

    new_version = current_version + 1
    record = ReviewDecision(
        anomaly_id=anomaly.id,
        fingerprint=anomaly.fingerprint,
        transaction_id=anomaly.transaction_id,
        decision=decision,
        reason=reason,
        version=new_version,
        expected_version=expected_version,
        run_id=run_id or anomaly.latest_run_id,
        analysis_id=anomaly.analysis_id,
        reviewer_id=user.id,
        reviewer_name=getattr(user, "display_name", "") or user.email,
    )
    db.add(record)
    anomaly.version = new_version
    anomaly.review_status = decision
    db.flush()
    return record


def _decision_payload(record: ReviewDecision | None) -> dict | None:
    if not record:
        return None
    return {
        "id": record.id,
        "decision": record.decision,
        "reason": record.reason,
        "version": record.version,
        "reviewer_id": record.reviewer_id,
        "reviewer_name": record.reviewer_name,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def review_summary(db: Session, analysis_id: str | None = None) -> dict:
    items = list_anomalies(db, analysis_id=analysis_id)
    summary = {ReviewStatus.PENDING.value: 0,
               ReviewStatus.FALSE_POSITIVE.value: 0,
               ReviewStatus.UNDER_INVESTIGATION.value: 0}
    for item in items:
        summary[item.review_status] = summary.get(item.review_status, 0) + 1
    summary["total"] = len(items)
    return summary
