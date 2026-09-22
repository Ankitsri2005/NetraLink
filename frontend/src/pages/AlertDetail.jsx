import { Link, useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getAlert, getPerson } from '../api/client'
import { fmtMoney, fmtNum, PRIORITY_COLORS } from '../components/theme'

function Gauge({ value }) {
  const pct = Math.min(100, Math.max(0, (Math.abs(Number(value) || 0) / 0.12) * 100))
  return (
    <div
      className="gauge"
      style={{ '--p': `${pct}%`, borderColor: PRIORITY_COLORS[value < 0 ? 'High' : 'Low'] }}
    >
      <div className="gauge-inner">
        <span className="gauge-num">{Number(value).toFixed(3)}</span>
        <span className="gauge-label">anomaly score</span>
      </div>
    </div>
  )
}

export default function AlertDetail() {
  const { personId } = useParams()
  const alert = useApi(() => getAlert(personId), [personId])
  const person = useApi(() => getPerson(personId), [personId])

  const a = alert.data

  return (
    <div className="page">
      {alert.loading && <div className="muted">Loading alert…</div>}
      {alert.error && <div className="muted error">Alert not found</div>}

      {a && (
        <>
          <div className="detail-head rise-in">
            <div>
              <span className="kicker">ALERT</span>
              <h2 className="detail-name">
                {a.name}
                <span
                  className="pri-badge big"
                  style={{ color: PRIORITY_COLORS[a.priority] }}
                >
                  {a.priority}
                </span>
              </h2>
              <p className="detail-id mono">{a.person_id}</p>
            </div>
            <div className="detail-actions">
              <Link to={`/persons/${a.person_id}`} className="btn primary">
                Entity panel
              </Link>
              <Link to={`/graph?focus=${a.person_id}`} className="btn ghost">
                Locate in network
              </Link>
            </div>
          </div>

          <div className="grid-detail">
            <div className="panel rise-in" style={{ animationDelay: '80ms' }}>
              <div className="panel-head"><h3>Risk dial</h3></div>
              <div className="gauge-wrap">
                <Gauge value={a.anomaly_score} />
              </div>
            </div>

            <div className="panel rise-in" style={{ animationDelay: '130ms' }}>
              <div className="panel-head"><h3>Signal stats</h3></div>
              <div className="stat-grid">
                <div className="mini-stat"><span>Calls</span><b>{fmtNum(a.total_calls)}</b></div>
                <div className="mini-stat"><span>Contacts</span><b>{fmtNum(a.unique_contacts)}</b></div>
                <div className="mini-stat"><span>Received</span><b className="pos">{fmtMoney(a.money_received)}</b></div>
                <div className="mini-stat"><span>Sent</span><b>{fmtMoney(a.money_sent)}</b></div>
                <div className="mini-stat"><span>Txns</span><b>{fmtNum(a.total_transactions)}</b></div>
                <div className="mini-stat"><span>Diff</span><b className={Number(a.money_difference) < 0 ? 'neg' : 'pos'}>{fmtMoney(a.money_difference)}</b></div>
                <div className="mini-stat"><span>Degree</span><b className="mono">{(a.degree_centrality ?? 0).toFixed(3)}</b></div>
                <div className="mini-stat"><span>Betweenness</span><b className="mono">{(a.betweenness_centrality ?? 0).toFixed(3)}</b></div>
              </div>
            </div>

            <div className="panel rise-in" style={{ animationDelay: '180ms' }}>
              <div className="panel-head"><h3>Why flagged</h3></div>
              <div className="chips">
                {(a.alert_reason || '').split(',').map((r) => (
                  <span key={r.trim()} className="chip">
                    {r.trim()}
                  </span>
                ))}
              </div>
            </div>

            <div className="panel rise-in" style={{ animationDelay: '230ms' }}>
              <div className="panel-head"><h3>Connected entities</h3></div>
              {person.loading && <div className="muted">Loading…</div>}
              {person.data && (
                <div className="entity-list">
                  <div className="entity-group">
                    <span className="group-label">Phones</span>
                    {person.data.persons_phones?.length ? (
                      person.data.persons_phones.map((p) => (
                        <div className="entity-row mono" key={p.phone_id}>
                          {p.phone_number}
                        </div>
                      ))
                    ) : (
                      <span className="muted">None</span>
                    )}
                  </div>
                  <div className="entity-group">
                    <span className="group-label">Accounts</span>
                    {person.data.accounts?.length ? (
                      person.data.accounts.map((ac) => (
                        <div className="entity-row" key={ac.account_id}>
                          <span className="mono">{ac.account_number}</span>
                          <span className="muted">{ac.bank}</span>
                        </div>
                      ))
                    ) : (
                      <span className="muted">None</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}