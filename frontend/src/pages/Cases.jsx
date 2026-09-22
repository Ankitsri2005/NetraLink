import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { createCase, getCases } from '../api/client'

const STATUS_COLORS = {
  open: '#12b76a',
  in_progress: '#f59e0b',
  closed: '#9aa0a6',
}

const fmtDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function Cases() {
  const navigate = useNavigate()
  const { data, loading, error, refetch } = useApi(getCases)
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [creating, setCreating] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [saveError, setSaveError] = useState(null)
  const [saving, setSaving] = useState(false)

  const rows = useMemo(() => {
    let r = data || []
    if (q.trim()) {
      const needle = q.trim().toLowerCase()
      r = r.filter(
        (c) =>
          (c.case_number || '').toLowerCase().includes(needle) ||
          (c.title || '').toLowerCase().includes(needle),
      )
    }
    if (status) r = r.filter((c) => c.status === status)
    return r
  }, [data, q, status])

  const submit = async (e) => {
    e.preventDefault()
    if (!title.trim()) return
    setSaving(true)
    setSaveError(null)
    try {
      const created = await createCase({ title: title.trim(), description: description.trim() || null })
      refetch()
      navigate(`/cases/${created.id}`)
    } catch (err) {
      setSaveError(err.message || 'Failed to create case')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <div className="toolbar rise-in">
        <input
          className="search"
          placeholder="Search case number or title…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select className="select" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In progress</option>
          <option value="closed">Closed</option>
        </select>
        <button
          type="button"
          className={`btn ${creating ? 'ghost' : 'primary'}`}
          onClick={() => {
            setCreating((v) => !v)
            setSaveError(null)
          }}
        >
          {creating ? 'Cancel' : '+ New case'}
        </button>
      </div>

      {creating && (
        <form className="panel case-create rise-in" onSubmit={submit}>
          <div className="panel-head">
            <h3>Register investigation</h3>
          </div>
          <div className="case-create-fields">
            <input
              className="search case-create-title"
              placeholder="Case title — e.g. Telecom fraud ring, Jaipur sector 12"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              autoFocus
            />
            <textarea
              className="case-create-desc"
              placeholder="Scope, persons of interest, known evidence…"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
          {saveError && <div className="muted error small">⚠ {saveError}</div>}
          <div className="case-create-actions">
            <button type="submit" className="btn primary small" disabled={saving || !title.trim()}>
              {saving ? 'Opening…' : 'Create case'}
            </button>
            <button
              type="button"
              className="btn ghost small"
              onClick={() => {
                setCreating(false)
                setSaveError(null)
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="panel table-panel rise-in" style={{ animationDelay: '80ms' }}>
        {loading && <div className="muted pad">Loading cases…</div>}
        {error && <div className="muted error pad">Failed to load cases</div>}
        {!loading && !error && !data?.length && (
          <div className="muted pad">
            No cases yet.{' '}
            <button type="button" className="btn small primary" onClick={() => setCreating(true)}>
              Create your first investigation
            </button>
          </div>
        )}
        {data && data.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Case</th>
                <th>Title</th>
                <th>Status</th>
                <th>Evidence</th>
                <th>Alerts</th>
                <th>Notes</th>
                <th>Opened</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id} onClick={() => navigate(`/cases/${c.id}`)}>
                  <td className="mono strong">{c.case_number}</td>
                  <td className="cell-name">
                    <span className="mini-dot" style={{ background: STATUS_COLORS[c.status] }} />
                    {c.title}
                  </td>
                  <td>
                    <span className="pri-badge" style={{ color: STATUS_COLORS[c.status] }}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="mono">{c.evidence_count}</td>
                  <td className="mono">{c.alert_count}</td>
                  <td className="mono">{c.note_count}</td>
                  <td className="muted">{fmtDate(c.created_at)}</td>
                </tr>
              ))}
              {!rows.length && (
                <tr>
                  <td colSpan={7} className="muted pad">
                    No cases match.
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