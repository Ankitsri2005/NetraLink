import { useEffect, useRef, useState, useCallback } from 'react'
import { NODE_COLORS, RELATION_COLORS } from './theme'

export default function GraphView({
  graph,
  selectedNodeId,
  onSelectNode,
  height = '65vh',
  filterType = null,
}) {
  const containerRef = useRef(null)
  const svgRef = useRef(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const transformRef = useRef({ zoom: 1, pan: { x: 0, y: 0 } })

  const stateRef = useRef({
    nodes: [],
    edges: [],
    map: new Map(),
    selectedNodeId,
    onSelectNode,
    filterType,
    isDraggingNode: false,
    draggedNode: null,
    isPanning: false,
    panStart: { x: 0, y: 0 },
    panOrigin: { x: 0, y: 0 },
    rafId: null,
    frameNum: 0,
    active: true,
  })

  // Sync props to refs
  stateRef.current.selectedNodeId = selectedNodeId
  stateRef.current.onSelectNode = onSelectNode
  stateRef.current.filterType = filterType
  transformRef.current = { zoom, pan }

  // Update zoom and pan smoothly
  const handleZoom = useCallback((delta, centerX, centerY) => {
    setZoom((prevZoom) => {
      const nextZoom = Math.min(Math.max(prevZoom * delta, 0.25), 4)
      if (centerX !== undefined && centerY !== undefined) {
        setPan((prevPan) => {
          const ratio = nextZoom / prevZoom
          const nextPanX = centerX - (centerX - prevPan.x) * ratio
          const nextPanY = centerY - (centerY - prevPan.y) * ratio
          return { x: nextPanX, y: nextPanY }
        })
      }
      return nextZoom
    })
  }, [])

  const resetView = useCallback(() => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }, [])

  // Center on node if selected
  useEffect(() => {
    if (!selectedNodeId || !stateRef.current.map.has(selectedNodeId)) return
    const n = stateRef.current.map.get(selectedNodeId)
    if (n && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      const cx = rect.width / 2
      const cy = rect.height / 2
      // Pan so node is at center
      setPan({ x: cx - n.x * transformRef.current.zoom, y: cy - n.y * transformRef.current.zoom })
    }
  }, [selectedNodeId])

  useEffect(() => {
    const svg = svgRef.current
    const container = containerRef.current
    if (!graph || !svg || !container) return

    const W = container.clientWidth || 900
    const H = container.clientHeight || 560
    setPan({ x: W / 2, y: H / 2 })

    // Initialize node positions in a compact radial pattern to avoid overlap
    const nodes = graph.nodes.map((n, i) => {
      const angle = (i / graph.nodes.length) * 2 * Math.PI
      const dist = 60 + Math.sqrt(i) * 26
      return {
        id: String(n.id),
        type: n.type,
        label: String(n.attributes?.name ?? n.id),
        x: Math.cos(angle) * dist,
        y: Math.sin(angle) * dist,
        vx: 0,
        vy: 0,
        fixed: false,
      }
    })

    const nodeMap = new Map(nodes.map((n) => [n.id, n]))
    const edges = graph.edges
      .map((e) => ({
        source: String(e.source),
        target: String(e.target),
        s: nodeMap.get(String(e.source)),
        t: nodeMap.get(String(e.target)),
        type: e.type,
      }))
      .filter((e) => e.s && e.t)

    stateRef.current.nodes = nodes
    stateRef.current.edges = edges
    stateRef.current.map = nodeMap
    stateRef.current.frameNum = 0
    stateRef.current.active = true

    const NS = 'http://www.w3.org/2000/svg'
    svg.innerHTML = ''

    // Root transform group for Pan/Zoom
    const worldGroup = document.createElementNS(NS, 'g')
    worldGroup.setAttribute('class', 'graph-world')
    svg.appendChild(worldGroup)

    const lineLayer = document.createElementNS(NS, 'g')
    lineLayer.setAttribute('class', 'graph-edges')
    const nodeLayer = document.createElementNS(NS, 'g')
    nodeLayer.setAttribute('class', 'graph-nodes')
    worldGroup.appendChild(lineLayer)
    worldGroup.appendChild(nodeLayer)

    // Build DOM elements for edges
    const edgeEls = edges.map((e) => {
      const line = document.createElementNS(NS, 'line')
      const c = RELATION_COLORS[e.type] || RELATION_COLORS.default
      line.setAttribute('stroke', c)
      line.setAttribute('stroke-width', '1.2')
      line.setAttribute('stroke-opacity', '0.35')
      if (e.type === 'CALLED') line.setAttribute('stroke-dasharray', '3 4')
      lineLayer.appendChild(line)
      return { line, e }
    })

    // Build DOM elements for nodes
    const elById = {}
    nodes.forEach((n) => {
      const g = document.createElementNS(NS, 'g')
      g.setAttribute('class', 'graph-node-group')
      g.setAttribute('cursor', 'pointer')

      const halo = document.createElementNS(NS, 'circle')
      const core = document.createElementNS(NS, 'circle')
      const lbl = document.createElementNS(NS, 'text')
      const tip = document.createElementNS(NS, 'title')

      tip.textContent = `${n.label || n.id} (${n.type})`
      g.appendChild(tip)
      g.appendChild(halo)
      g.appendChild(core)
      g.appendChild(lbl)

      const c = NODE_COLORS[n.type] || NODE_COLORS.default
      core.setAttribute('fill', c)
      halo.setAttribute('fill', 'none')
      halo.setAttribute('stroke', c)

      lbl.setAttribute('fill', '#2d3748')
      lbl.setAttribute('font-size', '10')
      lbl.setAttribute('font-weight', '500')
      lbl.setAttribute('dy', '-11')
      lbl.setAttribute('text-anchor', 'middle')
      lbl.setAttribute('pointer-events', 'none')
      lbl.textContent = n.label

      // Node pointer interaction (drag & select)
      let moved = false
      let startPoint = { x: 0, y: 0 }

      g.addEventListener('pointerdown', (ev) => {
        ev.stopPropagation()
        moved = false
        startPoint = { x: ev.clientX, y: ev.clientY }
        stateRef.current.isDraggingNode = true
        stateRef.current.draggedNode = n
        n.fixed = true
        stateRef.current.active = true
        g.setPointerCapture(ev.pointerId)
      })

      g.addEventListener('pointermove', (ev) => {
        if (!stateRef.current.isDraggingNode || stateRef.current.draggedNode !== n) return
        const dx = ev.clientX - startPoint.x
        const dy = ev.clientY - startPoint.y
        if (Math.hypot(dx, dy) > 4) moved = true

        const { zoom } = transformRef.current
        n.x += (ev.movementX || 0) / zoom
        n.y += (ev.movementY || 0) / zoom
        n.vx = 0
        n.vy = 0
        stateRef.current.frameNum = 0
        stateRef.current.active = true
      })

      const handlePointerUp = (ev) => {
        if (stateRef.current.isDraggingNode && stateRef.current.draggedNode === n) {
          stateRef.current.isDraggingNode = false
          stateRef.current.draggedNode = null
          n.fixed = false
          try {
            g.releasePointerCapture(ev.pointerId)
          } catch {}
          if (!moved) {
            stateRef.current.onSelectNode?.(n)
          }
        }
      }

      g.addEventListener('pointerup', handlePointerUp)
      g.addEventListener('pointercancel', handlePointerUp)

      nodeLayer.appendChild(g)
      elById[n.id] = { g, halo, core, lbl, n }
    })

    // Physics parameters (stable Coulomb + Hooke's Law + center pull)
    const kRep = 4500
    const rest = 65
    const ks = 0.035
    const gravity = 0.012
    const maxSpeed = 8

    let running = true

    const frame = (now) => {
      if (!running) return

      const { zoom, pan } = transformRef.current
      worldGroup.setAttribute('transform', `translate(${pan.x} ${pan.y}) scale(${zoom})`)

      const activeSel = stateRef.current.selectedNodeId
      const currentFilter = stateRef.current.filterType

      // Run physics steps only while active
      if (stateRef.current.active) {
        stateRef.current.frameNum++

        // Pairwise node repulsion
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i]
            const b = nodes[j]
            let dx = a.x - b.x
            let dy = a.y - b.y
            let d2 = dx * dx + dy * dy
            if (d2 < 4) {
              dx = (Math.random() - 0.5) * 4
              dy = (Math.random() - 0.5) * 4
              d2 = dx * dx + dy * dy || 4
            }
            const d = Math.sqrt(d2)
            // Softened force calculation
            const f = kRep / Math.max(d2, 250)
            const fx = (dx / d) * f
            const fy = (dy / d) * f
            a.vx += fx
            a.vy += fy
            b.vx -= fx
            b.vy -= fy
          }
        }

        // Spring attraction along edges
        for (const { s, t } of edges) {
          const dx = s.x - t.x
          const dy = s.y - t.y
          const d = Math.sqrt(dx * dx + dy * dy) || 0.001
          const f = (d - rest) * ks
          const fx = (dx / d) * f
          const fy = (dy / d) * f
          s.vx -= fx
          s.vy -= fy
          t.vx += fx
          t.vy += fy
        }

        // Apply damping, center-gravity, and max speed
        const damping = stateRef.current.frameNum > 100 ? 0.72 : 0.84
        let totalVel = 0

        for (const n of nodes) {
          if (n.fixed) {
            n.vx = 0
            n.vy = 0
            continue
          }
          // Center gravity
          n.vx += (0 - n.x) * gravity
          n.vy += (0 - n.y) * gravity
          n.vx *= damping
          n.vy *= damping

          const spd = Math.hypot(n.vx, n.vy)
          if (spd > maxSpeed) {
            n.vx = (n.vx / spd) * maxSpeed
            n.vy = (n.vy / spd) * maxSpeed
          }

          n.x += n.vx
          n.y += n.vy
          totalVel += spd
        }

        // Settle condition to save CPU
        if (stateRef.current.frameNum > 150 && totalVel / nodes.length < 0.05) {
          stateRef.current.active = false
        }
      }

      // Compute connected nodes for selection highlighting
      const connectedNodeIds = new Set()
      const connectedEdgeIndices = new Set()
      if (activeSel) {
        connectedNodeIds.add(activeSel)
        edges.forEach((ed, idx) => {
          if (ed.source === activeSel || ed.target === activeSel) {
            connectedEdgeIndices.add(idx)
            connectedNodeIds.add(ed.source)
            connectedNodeIds.add(ed.target)
          }
        })
      }

      // Update edge lines
      edgeEls.forEach(({ line, e }, idx) => {
        line.setAttribute('x1', e.s.x.toFixed(1))
        line.setAttribute('y1', e.s.y.toFixed(1))
        line.setAttribute('x2', e.t.x.toFixed(1))
        line.setAttribute('y2', e.t.y.toFixed(1))

        if (activeSel) {
          const isConnected = connectedEdgeIndices.has(idx)
          line.setAttribute('stroke-opacity', isConnected ? '0.85' : '0.08')
          line.setAttribute('stroke-width', isConnected ? '2.4' : '0.8')
        } else {
          line.setAttribute('stroke-opacity', '0.35')
          line.setAttribute('stroke-width', '1.2')
        }
      })

      // Update node elements
      const pulse = Math.sin(now / 150)
      for (const id in elById) {
        const { g, halo, core, lbl, n } = elById[id]
        g.setAttribute('transform', `translate(${n.x.toFixed(1)} ${n.y.toFixed(1)})`)

        const isSelected = activeSel === n.id
        const isConnected = !activeSel || connectedNodeIds.has(n.id)
        const matchesFilter = !currentFilter || n.type === currentFilter

        if (isSelected) {
          core.setAttribute('r', '9')
          core.setAttribute('opacity', '1')
          halo.setAttribute('stroke-width', '2.5')
          halo.setAttribute('r', `${14 + 3 * pulse}`)
          lbl.setAttribute('opacity', '1')
          lbl.setAttribute('font-weight', '700')
        } else if (isConnected && matchesFilter) {
          core.setAttribute('r', '5.5')
          core.setAttribute('opacity', '0.9')
          halo.setAttribute('stroke-width', '0')
          halo.setAttribute('r', '5.5')
          lbl.setAttribute('opacity', activeSel ? '0.85' : '0.6')
          lbl.setAttribute('font-weight', '500')
        } else {
          // Dim unconnected nodes
          core.setAttribute('r', '4')
          core.setAttribute('opacity', '0.15')
          halo.setAttribute('stroke-width', '0')
          lbl.setAttribute('opacity', '0.1')
        }
      }

      stateRef.current.rafId = requestAnimationFrame(frame)
    }

    stateRef.current.rafId = requestAnimationFrame(frame)

    return () => {
      running = false
      if (stateRef.current.rafId) {
        cancelAnimationFrame(stateRef.current.rafId)
      }
    }
  }, [graph])

  // Canvas Pan Handlers
  const handlePointerDownBg = (ev) => {
    if (ev.target.tagName !== 'svg') return
    stateRef.current.isPanning = true
    stateRef.current.panStart = { x: ev.clientX, y: ev.clientY }
    stateRef.current.panOrigin = { ...pan }
    ev.target.setPointerCapture(ev.pointerId)
  }

  const handlePointerMoveBg = (ev) => {
    if (!stateRef.current.isPanning) return
    const dx = ev.clientX - stateRef.current.panStart.x
    const dy = ev.clientY - stateRef.current.panStart.y
    setPan({
      x: stateRef.current.panOrigin.x + dx,
      y: stateRef.current.panOrigin.y + dy,
    })
  }

  const handlePointerUpBg = (ev) => {
    if (stateRef.current.isPanning) {
      stateRef.current.isPanning = false
      try {
        ev.target.releasePointerCapture(ev.pointerId)
      } catch {}
    }
  }

  const handleWheel = (ev) => {
    ev.preventDefault()
    const container = containerRef.current
    if (!container) return
    const rect = container.getBoundingClientRect()
    const mouseX = ev.clientX - rect.left
    const mouseY = ev.clientY - rect.top
    const delta = ev.deltaY < 0 ? 1.15 : 0.87
    handleZoom(delta, mouseX, mouseY)
  }

  return (
    <div
      ref={containerRef}
      className="graph-container"
      style={{ position: 'relative', width: '100%', height, overflow: 'hidden' }}
      onWheel={handleWheel}
    >
      {/* Zoom / Pan Navigation Controls */}
      <div className="graph-toolbar">
        <button
          type="button"
          className="graph-btn"
          title="Zoom In"
          onClick={() => {
            const rect = containerRef.current?.getBoundingClientRect()
            handleZoom(1.25, (rect?.width || 900) / 2, (rect?.height || 560) / 2)
          }}
        >
          +
        </button>
        <button
          type="button"
          className="graph-btn"
          title="Zoom Out"
          onClick={() => {
            const rect = containerRef.current?.getBoundingClientRect()
            handleZoom(0.8, (rect?.width || 900) / 2, (rect?.height || 560) / 2)
          }}
        >
          −
        </button>
        <button
          type="button"
          className="graph-btn"
          title="Reset View"
          onClick={resetView}
        >
          ⟲
        </button>
        <span className="graph-zoom-label">{Math.round(zoom * 100)}%</span>
      </div>

      <svg
        ref={svgRef}
        className="graph-svg"
        style={{ width: '100%', height: '100%', display: 'block', cursor: 'grab' }}
        onPointerDown={handlePointerDownBg}
        onPointerMove={handlePointerMoveBg}
        onPointerUp={handlePointerUpBg}
        onPointerCancel={handlePointerUpBg}
        onClick={(ev) => {
          if (ev.target.tagName === 'svg') {
            onSelectNode?.(null)
          }
        }}
      />
    </div>
  )
}