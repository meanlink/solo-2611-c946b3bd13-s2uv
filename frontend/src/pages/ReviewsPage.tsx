import { useState } from "react";
import { listAnomalies } from "../api/reviews";
import Panel from "../components/common/Panel";
import ReviewBadge from "../components/common/ReviewBadge";
import AnomalyDetailPanel from "../components/review/AnomalyDetailPanel";
import { PAGE_LABELS } from "../constants/domain";
import { REVIEW_STATUS_LABELS } from "../constants/enums";
import { useAsync } from "../hooks/useAsync";
import { dateTime } from "../utils/format";
import type { ReviewStatusValue } from "../types";

const STATUS_FILTERS: Array<ReviewStatusValue | ""> = ["", "pending", "false_positive", "under_investigation"];

export default function ReviewsPage() {
  const [statusFilter, setStatusFilter] = useState<ReviewStatusValue | "">("");
  const [merchant, setMerchant] = useState("");
  const [includeSuperseded, setIncludeSuperseded] = useState(false);
  const [selectedId, setSelectedId] = useState("");

  const { data, error, reload } = useAsync(
    () => listAnomalies({
      review_status: statusFilter,
      merchant: merchant.trim(),
      include_superseded: includeSuperseded,
    }),
    [statusFilter, merchant, includeSuperseded],
  );

  const selected = data?.items.find((item) => item.id === selectedId) || data?.items[0] || null;
  const summary = data?.summary;

  return (
    <>
      <header className="page-head">
        <div>
          <div className="eyebrow">{PAGE_LABELS[4]}</div>
          <h1>逐笔异常复核</h1>
          <p>
            同一商户夜间的多笔交易逐笔列出，可逐笔判为误报或待追查，记录理由、判定人与时间。
            同数据同规则重跑不重复建待办并沿用结论；数据或规则更新后重新复核，历史结论仍可追溯。
          </p>
        </div>
        <span className="method-tag">{data?.total ?? 0} 条待办</span>
      </header>

      {error && <div className="error-box">{error}</div>}

      {summary && (
        <div className="stat-row">
          <div className="stat">
            <div className="stat-label">待复核</div>
            <div className="stat-value">{summary.pending ?? 0}</div>
          </div>
          <div className="stat">
            <div className="stat-label">误报</div>
            <div className="stat-value">{summary.false_positive ?? 0}</div>
          </div>
          <div className="stat">
            <div className="stat-label">追查中</div>
            <div className="stat-value">{summary.under_investigation ?? 0}</div>
          </div>
          <div className="stat">
            <div className="stat-label">合计</div>
            <div className="stat-value">{summary.total ?? 0}</div>
          </div>
        </div>
      )}

      <Panel title="筛选待办">
        <div className="filter-bar">
          <div className="field">
            <label>复核状态</label>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as ReviewStatusValue | "")}>
              {STATUS_FILTERS.map((value) => (
                <option key={value} value={value}>
                  {value === "" ? "全部状态" : REVIEW_STATUS_LABELS[value]}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>商户</label>
            <input
              value={merchant}
              placeholder="按商户号搜索"
              onChange={(e) => setMerchant(e.target.value)}
            />
          </div>
          <div className="field">
            <label>历史代</label>
            <label style={{ display: "flex", alignItems: "center", gap: 8, textTransform: "none", letterSpacing: 0, minHeight: 40 }}>
              <input
                type="checkbox"
                checked={includeSuperseded}
                onChange={(e) => setIncludeSuperseded(e.target.checked)}
                style={{ minHeight: 0 }}
              />
              包含已被取代的历史待办
            </label>
          </div>
        </div>
      </Panel>

      {!data ? (
        <div className="empty">正在加载复核待办…</div>
      ) : data.items.length === 0 ? (
        <div className="empty">没有符合条件的异常交易。触发一次检测运行后将在此生成逐笔待办。</div>
      ) : (
        <div className="review-layout" style={{ marginTop: 26 }}>
          <Panel title="异常交易逐笔清单">
            <div style={{ overflowX: "auto" }}>
              <table className="table review-table">
                <thead>
                  <tr>
                    <th>交易号</th>
                    <th>商户</th>
                    <th>金额</th>
                    <th>时段</th>
                    <th>稳健 z</th>
                    <th>状态</th>
                    <th>版本</th>
                    <th>更新时间</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr
                      key={item.id}
                      className={`clickable ${selected?.id === item.id ? "selected" : ""} ${item.superseded ? "superseded-row" : ""}`}
                      onClick={() => setSelectedId(item.id)}
                    >
                      <td className="mono">{item.transaction_id}</td>
                      <td>{item.merchant}</td>
                      <td>{String(item.signal.amount ?? "—")}</td>
                      <td>{String(item.signal.hour ?? "—")}时</td>
                      <td>{String(item.signal.z ?? "—")}</td>
                      <td><ReviewBadge status={item.review_status} /></td>
                      <td className="mono">v{item.version}</td>
                      <td>{dateTime(item.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel title="复核详情与判定">
            {selected ? (
              // key 含版本号：判定提交后版本推进，面板重挂载并拉取最新结论与历史。
              <AnomalyDetailPanel key={`${selected.id}:${selected.version}`} anomaly={selected} onChanged={reload} />
            ) : (
              <div className="empty">请选择左侧一笔交易。</div>
            )}
          </Panel>
        </div>
      )}
    </>
  );
}
