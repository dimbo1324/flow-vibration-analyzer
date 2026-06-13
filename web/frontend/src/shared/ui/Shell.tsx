import { NavLink } from 'react-router-dom'
import { Activity, BarChart2, Upload } from 'lucide-react'

const NAV = [
  { to: '/',      label: 'Главная',         Icon: Activity },
  { to: '/demo',  label: 'Демо-анализ',     Icon: BarChart2 },
  { to: '/upload', label: 'Загрузка файла', Icon: Upload },
]

interface ShellProps {
  children: React.ReactNode
}

export function Shell({ children }: ShellProps) {
  return (
    <div className="flex min-h-screen flex-col bg-gray-950 text-white">
      {/* Top bar */}
      <header className="flex items-center gap-4 border-b border-gray-800 bg-gray-950 px-4 py-2 sticky top-0 z-20">
        <div className="flex items-center gap-2 mr-4">
          <Activity className="h-5 w-5 text-blue-500 flex-shrink-0" />
          <span className="text-sm font-semibold text-white hidden sm:block">IVA</span>
        </div>
        <nav className="flex items-center gap-1">
          {NAV.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                [
                  'flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition-colors',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white',
                ].join(' ')
              }
            >
              <Icon className="h-3.5 w-3.5 flex-shrink-0" />
              <span className="hidden sm:block">{label}</span>
            </NavLink>
          ))}
        </nav>
      </header>

      {/* Page content */}
      <main className="flex-1 overflow-x-hidden">
        <div className="mx-auto max-w-6xl px-4 py-6">
          {children}
        </div>
      </main>
    </div>
  )
}
