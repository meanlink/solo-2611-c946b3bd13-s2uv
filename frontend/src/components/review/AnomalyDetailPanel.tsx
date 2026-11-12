import { useEffect, useState } from "react";
import { getAnomaly, submitDecision } from "../../api/reviews";
import { ApiError } from "../../api/client";
import Button from "../common/Button";
import ReviewBadge from "../common/ReviewBadge";
import { REVIEW_DECISION_LABELS, REVIEW_STATUS_LABELS } from "../../constants/enums";
import { useAuth } from "../../hooks/useAuth";
import { checksum, dateTime } from "../../utils/format";
import type { Anomaly, AnomalyDetail, ReviewDecision, ReviewStatusValue } from "../../types";

interface Props {
  anomaly: Anomaly;
  onChanged: () => void;
}

export default function AnomalyDetailPanel({ anomaly, onChanged }: Props) {
  const user = useAuth();
  const [detail, setDetail] = useState<AnomalyDetail | null>(null);
  const [decision, setDecision] = useState<ReviewStatusValue>("false_positive");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState<ApiError["body"] | null>(null);

  const canReview = user?.role === "admin" || user?.role === "reviewer";

  useEffect(() => {
    setDetail(null);
    setError("");
    setConflict(null);
    setReason("");
    getAnomaly(anomaly.id).then(setDetail).catch((e) => setError((e as Error).message));
  }, [anomaly.id]);

  async function submit(expectedVersion: number) {
    if (!reason.trim()) {
      setError("请填写复核理由");
      return;
    }
    setBusy(true);
    setError("");
    setConflict(null);
    try {
      await submitDecision(anomaly.id, {
        decision,
        reason: reason.trim(),
        expected_version: expectedVersion,
      });
      setReason("");
      onChanged();
    } catch (e) {
      if (e instanceof ApiError && e.status === 409 && e.body.conflict) {
        // 并发冲突：展示前人最新结论，刷新详情后允许基于新版本重新判定。
        setConflict(e.body);
        const fresh = await getAnomaly(anomaly.id);
        setDetail(fresh);
      } else {
        setError((e as Error).message);
      }
    } finally {
      setBusy(false);
    }
  }

  const currentVersion = detail?.version ?? anomaly.version;

  return (
    <div className="content-grid">
      <div>
        <div className="panel-head">
          <h3 className="mono">{anomaly.transaction_id}</h3>
          <ReviewBadge status={anomaly.review_status} />
        </div>
        <p className="muted review-hint">
          商户 <strong>{anomaly.merchant || "—"}</strong> · 当前版本 v{currentVersion}
          {anomaly.superseded && " · 该待办已被新一代检测结果取代，仅供追溯"}
        </p>
        <table className="table">
          <tbody>
            {Object.entries(anomaly.signal).map(([key, value]) => (
              <tr key={key}>
                <th style={{ width: 110 }}>{key}</th>
                <td>{String(value)}</td>
              </tr>
            ))}
            <tr>
              <th>规则指纹</th>
              <td className="mono">{checksum(anomaly.rule_fingerprint)}</td>
            </tr>
            <tr>
              <th>数据指纹</th>
              <td className="mono">{checksum(anomaly.data_checksum)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {conflict?.latest_decision && (
        <div className="conflict-box">
          <strong>提交冲突：该交易已被其他复核员更新</strong>
          <span>
            最新结论：{REVIEW_STATUS_LABELS[conflict.latest_decision.decision]} ·
            v{conflict.latest_decision.version} · {conflict.latest_decision.reviewer_name} ·
            {dateTime(conflict.latest_decision.created_at)}
          </span>
          <span className="muted">理由：{conflict.latest_decision.reason}</span>
          <span className="muted">前人判断不会被覆盖；如需改判，请基于最新版本（v{currentVersion}）重新提交。</span>
        </div>
      )}
      {error && <div className="error-box">{error}</div>}

      {canReview && !anomaly.superseded && (
        <div className="decision-form">
          <div className="field">
            <label>逐笔判定</label>
            <div className="decision-actions">
              <Button
                primary={decision === "false_positive"}
                onClick={() => setDecision("false_positive")}
                type="button"
              >
                {REVIEW_DECISION_LABELS.false_positive}
              </Button>
              <Button
                primary={decision === "under_investigation"}
                onClick={() => setDecision("under_investigation")}
                type="button"
              >
                {REVIEW_DECISION_LABELS.under_investigation}
              </Button>
            </div>
          </div>
          <div className="field">
            <label>复核理由（必填）</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="说明判为误报或待追查的依据，例如商户夜间补货、历史流水吻合、需结合资金链路继续核查…"
            />
          </div>
          <Button primary disabled={busy} onClick={() => submit(currentVersion)}>
            {busy ? "提交中…" : `提交判定（基于 v${currentVersion}）`}
          </Button>
        </div>
      )}
      {!canReview && <p className="muted review-hint">当前角色仅可查看，复核判定需业务复核员或管理员提交。</p>}

      <div>
        <h3>判定历史（旧结论可追溯）</h3>
        {!detail ? (
          <div className="empty">正在加载历史…</div>
        ) : detail.decisions.length === 0 ? (
          <p className="muted">尚无判定记录。</p>
        ) : (
          <div className="timeline">
            {detail.decisions.map((d: ReviewDecision) => (
              <div className="timeline-item" key={d.id}>
                <div className="muted">
                  v{d.version} · {dateTime(d.created_at)} · {d.reviewer_name}
                </div>
                <ReviewBadge status={d.decision} />
                <p style={{ margin: "6px 0 0" }}>{d.reason}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
