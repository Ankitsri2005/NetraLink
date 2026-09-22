import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getGraph } from '../api/client'
import GraphView from '../components/GraphView'
import { NODE_COLORS, RELATION_COLORS } from '../components/theme'

const TYPES = ['Person', 'Phone', 'Account', 'Vehicle', 'Location', 'Fir', 'Incident']

export default function Graph() {
  const { data: graph, loading, error } = useApi(getGraph)
  const [params] = useSearchParams()
  const [sel, setSel] = useState(params.get('focus'))
  const [filterType, setFilterType] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const f = params.get('focus')
    if (f) setSel(f)
  }, [params])

  const selectedNode = useMemo(() => {
    if (!graph || !sel) return null
    return graph.nodes.find((n) => n.id === sel) || null
  }, [graph, sel])

  const neighbors = useMemo(() => {
    if (!graph || !sel) return []
    return graph.edges
      .filter((e) => e.source === sel || e.target === sel)
      .map((e) => {
        const otherId = e.source === sel ? e.target : e.source
        const otherNode = graph.nodes.find((n) => n.id === otherId)
        return {
          other: otherId,
          otherNode,
          rel: e.type,
          direction: e.source === sel ? '→' : '←',
        }
      })
  }, [graph, sel])

  const searchMatches = useMemo(() => {
    if (!graph || !searchQuery.trim()) return []
    const q = searchQuery.toLowerCase().trim()
    return graph.nodes
      .filter((n) => {
        const name = String(n.attributes?.name ?? '').toLowerCase()
        const id = String(n.id).toLowerCase()
        return name.includes(q) || id.includes(q)
      })
      .slice(0, 6)
  }, [graph, searchQuery])

  return (
    <div className="graph-page">
      <div className="graph-main panel rise-in">
        {loading && <div className="muted pad">Loading knowledge graph…</div>}
        {error && <div className="muted error pad">Failed to load graph</div>}
        {graph && (
          <GraphView
            graph={graph}
            selectedNodeId={sel}
            filterType={filterType}
            onSelectNode={(n) => setSel(n ? n.id : null)}
          />
        )}
      </div>

      <aside className="graph-side">
        {/* Search Panel */}
        <div className="panel rise-in" style={{ animationDelay: '40ms' }}>
          <div className="panel-head">
            <h3>Find in Network</h3>
          </div>
          <div className="graph-search-box">
            <input
              type="text"
              className="graph-search-input"
              placeholder="Search by name or ID (e.g. Rahul, P001)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                className="graph-search-clear"
                onClick={() => setSearchQuery('')}
              >
                ✕
              </button>
            )}
          </div>
          {searchMatches.length > 0 && (
            <div className="graph-search-results">
              {searchMatches.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className="graph-search-item"
                  onClick={() => {
                    setSel(m.id)
                    setSearchQuery('')
                  }}
                >
                  <span
                    className="legend-swatch"
                    style={{ background: NODE_COLORS[m.type] || NODE_COLORS.default }}
                  />
                  <b>{m.attributes?.name || m.id}</b>
                  <span className="muted small mono">{m.id}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Entity Types / Legend Panel */}
        <div className="panel rise-in" style={{ animationDelay: '80ms' }}>
          <div className="panel-head">
            <h3>Entity types</h3>
            {filterType && (
              <button
                type="button"
                className="btn small ghost"
                style={{ padding: '2px 8px', fontSize: '11px' }}
                onClick={() => setFilterType(null)}
              >
                Clear filter
              </button>
            )}
          </div>
          <div className="legend">
            {TYPES.map((t) => {
              const active = filterType === t
              return (
                <div
                  className={`legend-item filterable ${active ? 'active' : ''}`}
                  key={t}
                  onClick={() => setFilterType(filterType === t ? null : t)}
                  title={`Click to ${active ? 'clear' : 'filter'} ${t} entities`}
                  style={{
                    cursor: 'pointer',
                    padding: '4px 6px',
                    borderRadius: '6px',
                    background: active ? 'rgba(0,0,0,0.06)' : 'transparent',
                  }}
                >
                  <span className="legend-swatch" style={{ background: NODE_COLORS[t] }} />
                  <span>{t}</span>
                  <b className="mono">
                    {graph ? graph.nodes.filter((n) => n.type === t).length : '…'}
                  </b>
                </div>
              )
            })}
          </div>

          <div className="panel-head head-mt">
            <h3>Relationships</h3>
          </div>
          <div className="legend">
            {Object.entries(RELATION_COLORS)
              .filter(([k]) => k !== 'default')
              .map(([k, c]) => (
                <div className="legend-item" key={k}>
                  <span className="legend-swatch" style={{ background: c }} />
                  <span>{k}</span>
                </div>
              ))}
          </div>
        </div>

        {/* Selection Details Panel */}
        <div className="panel rise-in" style={{ animationDelay: '140ms' }}>
          <div className="panel-head">
            <h3>Selected Entity</h3>
            {sel && (
              <button
                type="button"
                className="btn small ghost"
                style={{ padding: '2px 8px', fontSize: '11px' }}
                onClick={() => setSel(null)}
              >
                Deselect
              </button>
            )}
          </div>

          {!sel && (
            <div className="muted" style={{ fontSize: '13px' }}>
              Click on any node or search above to inspect relationships. Drag nodes or pan/zoom the canvas to explore.
            </div>
          )}

          {sel && (
            <div className="sel-node">
              <div className="sel-title">
                <span
                  className="type-badge"
                  style={{
                    color: NODE_COLORS[selectedNode?.type || 'Entity'] || NODE_COLORS.default,
                  }}
                >
                  {selectedNode?.type || 'Entity'}
                </span>
                <b>{selectedNode?.attributes?.name || sel}</b>
              </div>
              <p className="mono mute small" style={{ margin: '2px 0 8px' }}>
                ID: {sel}
              </p>

              {/* Entity Attributes Preview */}
              {selectedNode?.attributes && Object.keys(selectedNode.attributes).length > 0 && (
                <div className="graph-attr-list">
                  {Object.entries(selectedNode.attributes)
                    .filter(([k]) => k !== 'name')
                    .slice(0, 4)
                    .map(([k, v]) => (
                      <div key={k} className="graph-attr-item">
                        <span className="muted">{k.replace('_', ' ')}:</span>
                        <b className="mono">{String(v)}</b>
                      </div>
                    ))}
                </div>
              )}

              {selectedNode?.type === 'Person' && (
                <Link
                  className="btn primary small"
                  style={{ marginTop: '10px', display: 'inline-block' }}
                  to={`/persons/${sel}`}
                >
                  Open entity panel →
                </Link>
              )}

              <div className="neighbors" style={{ marginTop: '14px' }}>
                <span className="group-label">Direct links ({neighbors.length})</span>
                {neighbors.slice(0, 15).map((n, i) => (
                  <button
                    key={i}
                    type="button"
                    className="neighbor-node"
                    onClick={() => setSel(n.other)}
                  >
                    <span className="mono">{n.direction}</span>
                    <span>{n.otherNode?.attributes?.name || n.other}</span>
                    <span
                      className="type-badge"
                      style={{
                        fontSize: '9px',
                        padding: '1px 5px',
                        color: NODE_COLORS[n.otherNode?.type] || '#888',
                      }}
                    >
                      {n.otherNode?.type}
                    </span>
                    <span className="muted small">{n.rel}</span>
                  </button>
                ))}
                {!neighbors.length && (
                  <span className="muted small">No direct connections found.</span>
                )}
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  )
}