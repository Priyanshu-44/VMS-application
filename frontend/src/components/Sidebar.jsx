import { NavLink } from 'react-router-dom'

const ICONS = {
  grid: 'M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z',
  events: 'M4 6h16M4 12h16M4 18h10',
  dashboard: 'M4 4h7v9H4V4zm9 0h7v5h-7V4zm0 9h7v7h-7v-7zM4 17h7v3H4v-3z',
  analytics: 'M4 20V10m6 10V4m6 16v-7m6 7V8',
  zones: 'M12 2l9 4.5v9L12 20l-9-4.5v-9L12 2z',
}

function Icon({ name, className = 'w-5 h-5' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
         strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d={ICONS[name]} />
    </svg>
  )
}

const NAV_ITEMS = [
  { to: '/', label: 'Live Grid', icon: 'grid', end: true },
  { to: '/events', label: 'Events', icon: 'events' },
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/analytics', label: 'Analytics', icon: 'analytics' },
  { to: '/zones', label: 'Zones', icon: 'zones' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 shrink-0 h-full bg-panel border-r border-border flex flex-col">
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent/20 border border-accent/40 flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="w-4.5 h-4.5 text-accent-2" fill="currentColor">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 2a8 8 0 110 16 8 8 0 010-16z" opacity=".4" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-semibold leading-tight">Smart VMS</div>
            <div className="text-[11px] text-text-dim leading-tight">A-1 Perimeter Security</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-accent/15 text-white border border-accent/30'
                  : 'text-text-dim hover:text-text hover:bg-panel-2 border border-transparent'
              }`
            }
          >
            <Icon name={item.icon} />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-border text-[11px] text-text-dim">
        False-alarm suppression: zones · class filter · dwell · cooldown
      </div>
    </aside>
  )
}
