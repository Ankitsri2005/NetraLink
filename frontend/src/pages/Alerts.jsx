import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getAlerts } from '../api/client'
import { fmtMoney, fmtNum, PRIORITY_COLORS } from '../components/theme'

export default function Alerts() {
  const navigate = useNavigate()
  const { data, loading, error } = useApi(() => getAlerts('?limit=200'))
  const [q, setQ] = useState('')
  const [pri, setPri] = useState('')
  const [sortKey, setSortKey] = useState('anomaly_score')
  const [dir, setDir] = useState('asc')

  const rows = useMemo(() => {
    let r = data || []
    if (q.trim()) {
      const needle = q.trim().toLowerCase()
      r = r.filter(
        (a) =>
          (a.name || '').toLowerCase().includes(needle) ||
          (a.person_id || '').toLowerCase().includes(needle),
      )
    }
    if (pri) r = r.filter((a) => (a.priority || '').toLowerCase() === pri.toLowerCase())
    return [...r].sort((a, b) => {
      const va = a[sortKey]
      const vb = b[sortKey]
      const d = (Number(va) || 0) - (Number(vb) || 0)
      return dir === 'asc' ? d : -d
    })
  }, [data, q, pri, sortKey, dir])

  const toggo = (k) => {
    if (sortKey === k) setDir(dir === 'asc' ? 'desc' : 'asc')
    else {
      setSortKey(k)
      setDir(k === 'anomaly_score' ? 'asc' : 'desc')
    }
  }

  return (
    <div className="page">
      <div className="toolbar rise-in">
        <input
          className="search"
          placeholder="Search name or ID…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select className="select" value={pri} onChange={(e) => setPri(e.target.value)}>
          <option value="">All priorities</option>
          <option>High</option>
          <option>Medium</option>
          <option>Low</option>
        </select>
      </div>

      <div className="panel table-panel rise-in" style={{ animationDelay: '80ms' }}>
        {loading && <div className="muted pad">Loading alerts…</div>}
        {error && <div className="muted error pad">Failed to load alerts</div>}
        {data && (
          <table className="table">
            <thead>
              <tr>
                <th onClick={() => toggo('person_id')}>ID</th>
                <th onClick={() => toggo('name')}>Name</th>
                <th onClick={() => toggo('priority')}>Priority</th>
                <th onClick={() => toggo('anomaly_score')}>Anomaly score</th>
                <th onClick={() => toggo('total_calls')}>Calls</th>
                <th onClick={() => toggo('unique_contacts')}>Contacts</th>
                <th onClick={() => toggo('money_received')}>Received</th>
                <th onClick={() => toggo('money_difference')}>Diff</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.person_id} onClick={() => navigate(`/alerts/${a.person_id}`)}>
                  <td className="mono">{a.person_id}</td>
                  <td className="strong cell-name">
                    <span
                      className="mini-dot"
                      style={{ background: PRIORITY_COLORS[a.priority] || '#8b93a7' }}
                    />
                    {a.name}
                  </td>
                  <td>
                    <span className="pri-badge" style={{ color: PRIORITY_COLORS[a.priority] }}>
                      {a.priority}
                    </span>
                  </td>
                  <td className="mono score-cell">{Number(a.anomaly_score).toFixed(3)}</td>
                  <td>{fmtNum(a.total_calls)}</td>
                  <td>{fmtNum(a.unique_contacts)}</td>
                  <td className="pos">{fmtMoney(a.money_received)}</td>
                  <td className={Number(a.money_difference) < 0 ? 'neg' : 'pos'}>
                    {fmtMoney(a.money_difference)}
                  </td>
                  <td className="cell-reason">{a.alert_reason}</td>
                </tr>
              ))}
              {!rows.length && (
                <tr>
                  <td colSpan={9} className="muted pad">
                    No alerts match.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}