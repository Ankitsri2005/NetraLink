import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '◈' },
  { to: '/alerts', label: 'Alerts', icon: '◇' },
  { to: '/graph', label: 'Network', icon: '⌬' },
  { to: '/cases', label: 'Cases', icon: '▦' },
]

export default function Layout() {
  const location = useLocation()
  const [page, setPage] = useState('NetraLink')

  useEffect(() => {
    const map = {
      '/': 'Dashboard',
      '/alerts': 'Alerts',
      '/graph': 'Network',
      '/cases': 'Cases',
    }
    const key = map[location.pathname]
    if (key) setPage(key)
    else if (location.pathname.startsWith('/alerts/')) setPage('Alert Detail')
    else if (location.pathname.startsWith('/persons/')) setPage('Entity Detail')
    else if (location.pathname.startsWith('/cases/')) setPage('Case Workbench')
  }, [location.pathname])

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <span className="brand-n1" />
            <span className="brand-n2" />
            <span className="brand-link" />
          </div>
          <div className="brand-text">
            <strong>Netra<span>Link</span></strong>
            <em>graph intelligence</em>
          </div>
        </div>

        <nav className="nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}          
        </nav>

        <div className="sidebar-foot">
          <div className="live-dot" />
          <span>Live</span>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <h1 className="page-title">{page}</h1>
          <div className="topbar-right">
            <div className="avatar">INV</div>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}