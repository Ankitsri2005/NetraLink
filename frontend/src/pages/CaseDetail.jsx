import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { addCaseNote, getCase, updateCase, uploadCaseEvidence } from '../api/client'

const STATUS_COLORS = {
  open: '#12b76a',
  in_progress: '#f59e0b',
  closed: '#9aa0a6',
}

const fmtStamp = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

const shortHash = (h) => (h ? h.slice(0, 12) + '…' + h.slice(-6) : '—')

export default function CaseDetail() {
  const { caseId } = useParams()
  const { data, loading, error, refetch } = useApi(() => getCase(caseId), [caseId])

  const [noteBody, setNoteBody] = useState('')
  const [noteAuthor, setNoteAuthor] = useState('')
  const [savingNote, setSavingNote] = useState(false)

  const [sourceType, setSourceType] = useState('cdr')
  const [file, setFile] = useState(null)
  const [fileKey, setFileKey] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState(null)
  const [uploadError, setUploadError] = useState(null)

  const [changingStatus, setChangingStatus] = useState(false)
  const [actionError, setActionError] = useState(null)

  const c = data

  const changeStatus = async (e) => {
    const next = e.target.value
    if (!c || next === c.status) return
    setChangingStatus(true)
    setActionError(null)
    try {
      await updateCase(c.id, { status: next })
      refetch()
    } catch (err) {
      setActionError(err.message || 'Failed to update status')
      e.target.value = c.status
    } finally {
      setChangingStatus(false)
    }
  }

  const submitNote = async (e) => {
    e.preventDefault()
    if (!noteBody.trim()) return
    setSavingNote(true)
    setActionError(null)
    try {
      await addCaseNote(c.id, { body: noteBody.trim(), author: noteAuthor.trim() || null })
      setNoteBody('')
      refetch()
    } catch (err) {
      setActionError(err.message || 'Failed to save note')
    } finally {
      setSavingNote(false)
    }
  }

  const submitEvidence = async (e) => {
    e.preventDefault()
    if (!file) {
      setUploadError('Choose a CDR file first.')
      return
    }
    setUploading(true)
    setUploadMsg(null)
    setUploadError(null)
    try {
      const res = await uploadCaseEvidence(c.id, sourceType, file)
      if (res.duplicate) {
        setUploadMsg(`“${res.file_name}” was already on the ledger (SHA-256 ${shortHash(res.content_hash)}) — no duplicate created.`)
      } else {
        const rels = res.summary?.relationships || {}
        const calls = rels.CALLED || 0
        const phones = res.summary?.nodes?.Phone || 0
        const linked = res.neo4j
          ? `linked ${calls} calls and ${phones} phones into the Neo4j graph`
          : 'stored as evidence (Neo4j offline — visible in the Network tab after restart)'
        setUploadMsg(`Processed “${res.file_name}” — ${linked}.`)
      }
      setFile(null)
      setFileKey((k) => k + 1)
      refetch()
    } catch (err) {
      setUploadError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="page">
      {loading && <div className="muted">Loading case…</div>}
      {error && <div className="muted error">Case not found</div>}

      {c && (
        <>
          <div className="detail-head rise-in">
            <div>
              <span className="kicker">CASE</span>
              <h2 className="detail-name">{c.title}</h2>
              <p className="detail-id mono">
                {c.case_number} · opened {fmtStamp(c.created_at)}
              </p>
            </div>
            <div className="detail-actions">
              <select
                className="select"
                value={c.status}
                onChange={changeStatus}
                disabled={changingStatus}
                style={{ color: STATUS_COLORS[c.status], fontWeight: 700 }}
              >
                <option style={{ color: '#111' }} value="open">open</option>
                <option style={{ color: '#111' }} value="in_progress">in progress</option>
                <option style={{ color: '#111' }} value="closed">closed</option>
              </select>
              <Link to="/graph" className="btn primary">
                Explore network →
              </Link>
            </div>
          </div>

          <div className="case-stats rise-in" style={{ animationDelay: '60ms' }}>
            <div className="case-stat">
              <b>{c.evidence_count}</b>
              <span>Evidence items</span>
            </div>
            <div className="case-stat">
              <b>{c.alert_count}</b>
              <span>Linked alerts</span>
            </div>
            <div className="case-stat">
              <b>{c.note_count}</b>
              <span>Investigator notes</span>
            </div>
            <div className="case-stat">
              <b className="mono" style={{ fontSize: 15, textTransform: 'uppercase' }}>
                {c.status.replace('_', ' ')}
              </b>
              <span>Current status</span>
            </div>
          </div>

          {actionError && <div className="muted error small pad">⚠ {actionError}</div>}

          <div className="grid-detail">
            <div className="panel rise-in" style={{ animationDelay: '120ms' }}>
              <div className="panel-head">
                <h3>Intelligence scope</h3>
              </div>
              <p className="case-desc">
                {c.description || (
                  <span className="muted">No scope described yet. Add notes as investigation progresses.</span>
                )}
              </p>
              <div className="panel-foot">
                <Link to="/alerts">Scan the network for linked anomalies →</Link>
              </div>
            </div>

            <div className="panel rise-in" style={{ animationDelay: '180ms' }}>
              <div className="panel-head">
                <h3>Evidence ledger</h3>
              </div>

              <form className="evidence-intake" onSubmit={submitEvidence}>
                <div className="evidence-intake-row">
                  <select
                    className="select"
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                    disabled={uploading}
                  >
                    <option value="cdr">CDR · call detail records</option>
                  </select>
                  <input
                    key={fileKey}
                    type="file"
                    accept=".csv,text/csv"
                    className="file-input"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    disabled={uploading}
                  />
                  <button type="submit" className="btn primary small" disabled={uploading || !file}>
                    {uploading ? 'Processing…' : 'Upload & link'}
                  </button>
                </div>
                <div className="evidence-hint">
                  NetraLink will extract phones, calls and tower locations into the investigation graph.
                  Columns:{' '}
                  <span className="mono">
                    call_id, caller_phone, receiver_phone, date_time, duration, tower_location
                  </span>
                </div>
                {uploadMsg && (
                  <div className="upload-ok small">
                    <b>✓</b> {uploadMsg}
                  </div>
                )}
                {uploadError && <div className="muted error small">⚠ {uploadError}</div>}
              </form>

              <div className="evidence-list">
                {c.evidence.map((ev) => (
                  <div className="evidence-item" key={ev.id}>
                    <div className="evidence-top">
                      <span className="type-badge">{ev.source_type.replace('_', ' ')}</span>
                      <span className="mono small muted">{ev.source_record_id}</span>
                    </div>
                    {ev.file_name && <div className="evidence-file">{ev.file_name}</div>}
                    <div className="evidence-hash mono small">
                      <span className="muted">SHA-256</span> {shortHash(ev.content_hash)}
                    </div>
                    {ev.previous_hash && (
                      <div className="evidence-hash mono small">
                        <span className="muted">prev</span> {shortHash(ev.previous_hash)}
                      </div>
                    )}
                    <div className="muted small">{fmtStamp(ev.created_at)}</div>
                  </div>
                ))}
                {!c.evidence.length && (
                  <div className="muted" style={{ fontSize: 13 }}>
                    No evidence yet — upload a CDR above and NetraLink will extract phones, calls and
                    locations into the graph.
                  </div>
                )}
              </div>
            </div>

            <div className="panel rise-in" style={{ animationDelay: '240ms' }}>
              <div className="panel-head">
                <h3>Investigation notes</h3>
              </div>
              <form className="note-form" onSubmit={submitNote}>
                <input
                  className="search note-author"
                  placeholder="Your name (optional)"
                  value={noteAuthor}
                  onChange={(e) => setNoteAuthor(e.target.value)}
                />
                <textarea
                  className="note-body"
                  placeholder="Record findings, sources, interview notes, hypotheses…"
                  value={noteBody}
                  onChange={(e) => setNoteBody(e.target.value)}
                  rows={3}
                />
                <div className="case-create-actions">
                  <button type="submit" className="btn primary small" disabled={savingNote || !noteBody.trim()}>
                    {savingNote ? 'Saving…' : 'Log note'}
                  </button>
                </div>
              </form>

              <div className="notes-list">
                {!c.notes.length && <div className="muted small">No notes yet.</div>}
                {c.notes.map((n) => (
                  <div className="note-item" key={n.id}>
                    <div className="note-meta">
                      <b>{n.author || 'Anonymous'}</b>
                      <span className="muted small mono">{fmtStamp(n.created_at)}</span>
                    </div>
                    <p className="note-body-text">{n.body}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}