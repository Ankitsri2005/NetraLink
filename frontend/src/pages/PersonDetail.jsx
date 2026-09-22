import { Link, useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getPerson, getAlert } from '../api/client'
import { fmtMoney, fmtNum, PRIORITY_COLORS, NODE_COLORS } from '../components/theme'

export default function PersonDetail() {
  const { personId } = useParams()
  const person = useApi(() => getPerson(personId), [personId])
  const alert = useApi(() => getAlert(personId), [personId])
  const p = person.data

  return (
    <div className="page">
      {person.loading && <div className="muted">Loading entity…</div>}
      {person.error && <div className="muted error">Entity not found</div>}

      {p && (
        <>
          <div className="detail-head rise-in">
            <div>
              <span className="kicker">ENTITY</span>
              <h2 className="detail-name">
                <span className="type-badge" style={{ color: NODE_COLORS.Person }}>
                  Person
                </span>
                {p.name}
              </h2>
              <p className="detail-id mono">{p.person_id} · {p.city || '—'} · age {p.age ?? '—'}</p>
            </div>
            <div className="detail-actions">
              {alert.data && (
                <span
                  className="pri-badge big pulse-badge"
                  style={{ color: PRIORITY_COLORS[alert.data.priority] }}
                >
                  ⚠ {alert.data.priority} alert
                </span>
              )}
              <Link to={`/graph?focus=${p.person_id}`} className="btn primary">
                View in network
              </Link>
            </div>
          </div>

          <div className="grid-detail">
            <div className="panel rise-in" style={{ animationDelay: '80ms' }}>
              <div className="panel-head"><h3>Anomaly profile</h3></div>
              <div className="stat-grid">
                <div className="mini-stat"><span>Score</span><b className="mono">{(p.anomaly_score ?? 0).toFixed(3)}</b></div>
                <div className="mini-stat"><span>Priority</span><b style={{ color: PRIORITY_COLORS[p.priority] }}>{p.priority ?? '—'}</b></div>
                <div className="mini-stat"><span>Calls</span><b>{fmtNum(p.total_calls)}</b></div>
                <div className="mini-stat"><span>Contacts</span><b>{fmtNum(p.unique_contacts)}</b></div>
                <div className="mini-stat"><span>Received</span><b className="pos">{fmtMoney(p.money_received)}</b></div>
                <div className="mini-stat"><span>Sent</span><b>{fmtMoney(p.money_sent)}</b></div>
                <div className="mini-stat"><span>Txns</span><b>{fmtNum(p.total_transactions)}</b></div>
                <div className="mini-stat"><span>Diff</span><b className={Number(p.money_difference) < 0 ? 'neg' : 'pos'}>{fmtMoney(p.money_difference)}</b></div>
              </div>
            </div>

            <div className="panel rise-in" style={{ animationDelay: '130ms' }}>
              <div className="panel-head"><h3>Owned phones</h3></div>
              <div className="entity-list">
                {(p.persons_phones || []).map((ph) => (
                  <div className="entity-row mono" key={ph.phone_id}>
                    {ph.phone_number}
                    <span className="muted">{ph.phone_id}</span>
                  </div>
                ))}
                {!p.persons_phones?.length && <span className="muted">No phones linked.</span>}
              </div>
            </div>

            <div className="panel rise-in" style={{ animationDelay: '180ms' }}>
              <div className="panel-head"><h3>Owned accounts</h3></div>
              <div className="entity-list">
                {(p.accounts || []).map((ac) => (
                  <div className="entity-row" key={ac.account_id}>
                    <span className="mono">{ac.account_number}</span>
                    <span className="muted">{ac.bank}</span>
                  </div>
                ))}
                {!p.accounts?.length && <span className="muted">No accounts linked.</span>}
              </div>
            </div>

            <div className="panel rise-in" style={{ animationDelay: '230ms' }}>
              <div className="panel-head"><h3>Linked alert</h3></div>
              {alert.loading && <div className="muted">Loading…</div>}
              {alert.data ? (
                <div className="alert-summary">
                  <div className="chips">
                    {(alert.data.alert_reason || '').split(',').map((r) => (
                      <span key={r.trim()} className="chip">{r.trim()}</span>
                    ))}
                  </div>
                  <Link className="btn primary small" to={`/alerts/${p.person_id}`}>
                    Open alert
                  </Link>
                </div>
              ) : (
                !alert.loading && !alert.error && <div className="muted">No alert flag for this person.</div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}