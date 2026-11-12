from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.controllers import review_controller
from src.database import get_db
from src.middlewares.auth import get_current_user, require_roles
from src.schemas.review import (
    AnomalyDetail,
    AnomalyList,
    ReviewDecisionCreate,
    ReviewDecisionRead,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=AnomalyList)
def index(
    analysis_id: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    merchant: str | None = Query(default=None),
    include_superseded: bool = Query(default=False),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return review_controller.list_items(
        db, analysis_id, review_status, include_superseded, merchant
    )


@router.get("/{anomaly_id}", response_model=AnomalyDetail)
def detail(anomaly_id: str, db: Session = Depends(get_db),
           user=Depends(get_current_user)):
    return review_controller.get_item(db, anomaly_id)


@router.get("/transaction/{transaction_id}/history",
            response_model=list[ReviewDecisionRead])
def transaction_history(transaction_id: str, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    return review_controller.history(db, transaction_id)


@router.post("/{anomaly_id}/decisions", response_model=ReviewDecisionRead)
def decide(anomaly_id: str, payload: ReviewDecisionCreate,
           db: Session = Depends(get_db),
           user=Depends(require_roles("admin", "reviewer"))):
    return review_controller.decide(db, anomaly_id, payload, user)
