import { Link } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getAlerts, getAlertSummary, getFirEntities, getGraph, getPersons, getTransactions } from '../api/client'
import StatCard from '../components/StatCard'
import { PRIORITY_COLORS } from '../components/theme'

export default function Dashboard() {
  const summary = useApi(getAlertSummary)
  const persons = useApi(getPersons)
  const graph = useApi(getGraph)
  const txns = useApi(() => getTransactions('?limit=200'))
  const fir = useApi(getFirEntities)
  const alerts = useApi(() => getAlerts('?limit=5'))

  const totalTxns = txns.data?.length || 0
  const totalAmount = txns.data?.reduce((s, t) => s + (Number(t.amount) || 0), 0) || 0

  return (
    <div className="page">
      <section className="hero">
        <div className="hero-radar" />
        <div className="hero-grid" />
        <div className="hero-content">
          <span className="hero-kicker">Network · Evidence · Intelligence</span>
          <h2 className="hero-title">Investigation Graph Intelligence</h2>
          <p className="hero-sub">
            Anomaly-scored entities from telecom and financial records, linked into one searchable network.
          </p>
          <div className="hero-cta">
            <Link to="/alerts">Review alerts <span>→</span></Link>
            <Link to="/graph" className="ghost">Explore network</Link>
          </div>
        </div>
        <div className="hero-pulse" aria-hidden="true" />
      </section>

      <section className="cards">
        <StatCard
          icon="⚠"
          label="Active alerts"
          value={summary.data?.total || 0}
          sub="flagged entities"
          accent="#e60023"
        />
        <StatCard
          icon="▲"
          label="High priority"
          value={summary.data?.by_priority?.High || 0}
          sub="needs immediate review"
          accent="#ff7a00"
          delay={60}
        />
        <StatCard
          icon="◎"
          label="Persons tracked"
          value={persons.data?.length || 0}
          sub="anomaly scored"
          accent="#12b76a"
          delay={120}
        />
        <StatCard
          icon="⌬"
          label="Graph entities"
          value={graph.data?.nodes?.length || 0}
          sub={`${graph.data?.edges?.length || 0} relationships`}
          accent="#8b5cf6"
          delay={180}
        />
        <StatCard
          icon="₹"
          label="Txns moved"
          value={totalTxns}
          sub={`₹${Math.round(totalAmount / 100000) / 10}L total`}
          accent="#f59e0b"
          delay={240}
        />
        <StatCard
          icon="◇"
          label="IR matches"
          value={fir.data?.length || 0}
          sub="from FIR reports"
          accent="#ec4899"
          delay={300}
        />
      </section>

      <section className="grid-two">
        <div className="panel rise-in" style={{ animationDelay: '320ms' }}>
          <div className="panel-head">
            <h3>Priority distribution</h3>
          </div>
          <div className="priority-bars">
            {(summary.data?.by_priority && Object.entries(summary.data.by_priority).map(([k, v]) => (
              <div className="pbar" key={k}>
                <span className="pbar-label">
                  {k}
                  <b>{v}</b>
                </span>
                <div className="pbar-track">
                  <div
                    className="pbar-fill"
                    style={{
                      width: `${summary.data.total ? (v / summary.data.total) * 100 : 0}%`,
                      background: PRIORITY_COLORS[k] || '#8b93a7',
                    }}
                  />
                </div>
              </div>
            ))) || <div className="muted">Loading…</div>}
          </div>
          <div className="panel-foot">
            <Link to="/alerts">Open alerts table →</Link>
          </div>
        </div>

        <div className="panel rise-in" style={{ animationDelay: '380ms' }}>
          <div className="panel-head">
            <h3>Top signals</h3>
          </div>
          {alerts.loading && <div className="muted">Loading…</div>}
          {alerts.error && <div className="muted error">Failed to load alerts</div>}
          {alerts.data && (
            <ul className="mini-list">
              {alerts.data.map((a) => (
                <li key={a.person_id}>
                  <Link to={`/alerts/${a.person_id}`} className="mini-item">
                    <span
                      className="mini-dot"
                      style={{ background: PRIORITY_COLORS[a.priority] || '#8b93a7' }}
                    />
                    <span className="mini-name">{a.name}</span>
                    <span className="mini-score">{Number(a.anomaly_score).toFixed(3)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  )
}