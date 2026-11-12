from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    REVIEWER = "reviewer"


class EntityStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisKind(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class ReviewStatus(StrEnum):
    PENDING = "pending"          # 待追查 / 待复核
    FALSE_POSITIVE = "false_positive"  # 误报
    UNDER_INVESTIGATION = "under_investigation"  # 待追查（已受理，需继续核查）


# 复核员可提交的逐笔判定（pending 为初始态，不允许由人工提交）。
REVIEW_DECISIONS = (
    ReviewStatus.FALSE_POSITIVE.value,
    ReviewStatus.UNDER_INVESTIGATION.value,
)
