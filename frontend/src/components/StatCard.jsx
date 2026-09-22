import { useEffect, useRef } from 'react'

export default function StatCard({ label, value, sub, accent = '#e60023', delay = 0, icon }) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const target = Number(value) || 0
    let cur = 0
    const start = performance.now()
    const dur = 900
    let raf
    const tick = (now) => {
      const p = Math.min(1, (now - start) / dur)
      const eased = 1 - Math.pow(1 - p, 3)
      cur = target * eased
      el.textContent = Math.round(cur).toLocaleString('en-IN')
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value])

  return (
    <div
      className="stat-card rise-in"
      style={{ '--accent': accent, animationDelay: `${delay}ms` }}
    >
      <div className="stat-icon" style={{ background: `${accent}18`, color: accent }}>
        {icon}
      </div>
      <div className="stat-body">
        <span className="stat-num">
          <span ref={ref}>0</span>
        </span>
        <span className="stat-label">{label}</span>
        {sub && <span className="stat-sub">{sub}</span>}
      </div>
    </div>
  )
}