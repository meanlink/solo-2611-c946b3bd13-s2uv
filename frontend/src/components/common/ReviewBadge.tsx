import { REVIEW_STATUS_LABELS } from "../../constants/enums";

export default function ReviewBadge({ status }: { status: string }) {
  return (
    <span className={`review-badge ${status}`}>
      {REVIEW_STATUS_LABELS[status] || status}
    </span>
  );
}
