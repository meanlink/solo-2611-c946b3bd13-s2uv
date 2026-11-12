import { Link, useParams } from "react-router-dom";
import { getRun } from "../api/runs";
import BarChart from "../components/common/BarChart";
import Button from "../components/common/Button";
import Panel from "../components/common/Panel";
import Stat from "../components/common/Stat";
import StatusBadge from "../components/common/StatusBadge";
import { PAGE_LABELS } from "../constants/domain";
import { useAsync } from "../hooks/useAsync";
import { checksum, dateTime } from "../utils/format";

export default function RunDetailPage() {
  const { runId } = useParams();
  const { data, error } = useAsync(() => getRun(runId || ""), [runId]);

  if (!data) {
    return (
      <>
        <header className="page-head">
          <div>
            <div className="eyebrow">{PAGE_LABELS[3]}</div>
            <h1>判读结果</h1>
          </div>
        </header>
        {error ? <div className="error-box">{error}</div> : <div className="empty">正在读取结果…</div>}
      </>
    );
  }

  const flagged = data.result.flagged || [];
  const sync = data.review_sync ?? { created: 0, reused: 0, total: 0 };

  return (
    <>
      <header className="page-head">
        <div>
          <div className="eyebrow">{PAGE_LABELS[3]}</div>
          <h1>判读结果</h1>
        </div>
        <StatusBadge status={data.status} />
      </header>

      {error && <div className="error-box">{error}</div>}

      <div className="content-grid">
        <section>
          <span className="method-tag">{data.result.method}</span>
          <h2 className="run-headline" style={{ marginTop: 18 }}>{data.result.headline}</h2>
          <p className="muted" style={{ maxWidth: 800, lineHeight: 1.8 }}>{data.result.narrative}</p>
        </section>

        <div className="stat-row">
          {data.result.metrics.map((metric) => (
            <Stat key={metric.label} label={metric.label} value={metric.value} unit={metric.unit} tone={metric.tone} />
          ))}
        </div>

        <div className="content-grid grid-main">
          <Panel title="效应与分组"><BarChart series={data.result.series} /></Panel>
          <Panel title="运行证据">
            <div className="content-grid">
              <div><span className="eyebrow">checksum</span><div className="mono">{checksum(data.checksum)}</div></div>
              <div><span className="eyebrow">rule fingerprint</span><div className="mono">{checksum(data.rule_fingerprint || "")}</div></div>
              <div><span className="eyebrow">created</span><p>{dateTime(data.created_at)}</p></div>
              <div><span className="eyebrow">run id</span><div className="mono">{data.id}</div></div>
            </div>
          </Panel>
        </div>

        <Panel
          title="逐笔复核待办同步"
          action={<Link className="button primary" to="/reviews">前往复核台</Link>}
        >
          <p className="muted" style={{ lineHeight: 1.8 }}>
            本次命中 {flagged.length} 笔异常交易；新建待办 {sync.created ?? 0} 条、
            复用已有待办 {sync.reused ?? 0} 条。同数据同规则重复运行不重复建待办，已有结论继续沿用。
          </p>
          <Link to="/reviews"><Button>逐笔判定误报 / 待追查</Button></Link>
        </Panel>

        <Panel title={`全部异常交易（${flagged.length} 笔，同一商户多笔逐笔列出）`}>
          {flagged.length === 0 ? (
            <div className="empty">本次运行没有命中异常交易。</div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>交易号</th><th>商户</th><th>金额</th><th>时段</th>
                    <th>速度</th><th>异常分</th><th>稳健 z</th>
                  </tr>
                </thead>
                <tbody>
                  {flagged.map((row) => (
                    <tr key={row.transaction_id}>
                      <td className="mono">{row.transaction_id}</td>
                      <td>{row.merchant}</td>
                      <td>{row.amount}</td>
                      <td>{row.hour}时</td>
                      <td>{row.velocity}</td>
                      <td>{row.score}</td>
                      <td>{row.z}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        <Panel title="算法限制"><p className="caveat">{data.result.caveat}</p></Panel>
        <Panel title="结果表（Top 20 排序样本）">
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>{Object.keys(data.result.table[0] || {}).map((column) => <th key={column}>{column}</th>)}</tr>
              </thead>
              <tbody>
                {data.result.table.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value, i) => <td key={i}>{typeof value === "object" ? JSON.stringify(value) : String(value ?? "—")}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </>
  );
}
