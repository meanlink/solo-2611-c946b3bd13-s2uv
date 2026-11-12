import { api } from "./client";
import type { Anomaly, AnomalyDetail, AnomalyListResponse, ReviewDecision, ReviewStatusValue } from "../types";

export interface ReviewQuery {
  analysis_id?: string;
  review_status?: ReviewStatusValue | "";
  merchant?: string;
  include_superseded?: boolean;
}

export function listAnomalies(query: ReviewQuery = {}): Promise<AnomalyListResponse> {
  const params = new URLSearchParams();
  if (query.analysis_id) params.set("analysis_id", query.analysis_id);
  if (query.review_status) params.set("review_status", query.review_status);
  if (query.merchant) params.set("merchant", query.merchant);
  if (query.include_superseded) params.set("include_superseded", "true");
  const qs = params.toString();
  return api<AnomalyListResponse>(`/reviews${qs ? `?${qs}` : ""}`);
}

export function getAnomaly(id: string): Promise<AnomalyDetail> {
  return api<AnomalyDetail>(`/reviews/${id}`);
}

export function getTransactionHistory(transactionId: string): Promise<ReviewDecision[]> {
  return api<ReviewDecision[]>(`/reviews/transaction/${encodeURIComponent(transactionId)}/history`);
}

export function submitDecision(
  id: string,
  payload: { decision: ReviewStatusValue; reason: string; expected_version: number },
): Promise<ReviewDecision> {
  return api<ReviewDecision>(`/reviews/${id}/decisions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
