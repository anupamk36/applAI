import { Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { useAuth } from './lib/auth'
import { LoginPage } from './pages/LoginPage'
import { ResumePage } from './pages/ResumePage'
import { JobsPage } from './pages/JobsPage'
import { PreferencesPage } from './pages/PreferencesPage'
import { OpportunityReportPage } from './pages/OpportunityReportPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function Shell({ children }: { children: React.ReactNode }) {
  const { token, logout } = useAuth()
  return (
    <div className="min-h-screen bg-white">
      {token && (
        <nav className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <div className="flex gap-4 text-sm font-medium text-gray-700">
            <NavLink to="/resume" className={({ isActive }) => (isActive ? 'text-gray-900' : '')}>
              Resume &amp; Facts
            </NavLink>
            <NavLink to="/jobs" className={({ isActive }) => (isActive ? 'text-gray-900' : '')}>
              Jobs
            </NavLink>
            <NavLink
              to="/opportunity-report"
              className={({ isActive }) => (isActive ? 'text-gray-900' : '')}
            >
              Opportunity Report
            </NavLink>
            <NavLink
              to="/preferences"
              className={({ isActive }) => (isActive ? 'text-gray-900' : '')}
            >
              Preferences
            </NavLink>
          </div>
          <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-800">
            Log out
          </button>
        </nav>
      )}
      {children}
    </div>
  )
}

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/resume"
          element={
            <RequireAuth>
              <ResumePage />
            </RequireAuth>
          }
        />
        <Route
          path="/jobs"
          element={
            <RequireAuth>
              <JobsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/preferences"
          element={
            <RequireAuth>
              <PreferencesPage />
            </RequireAuth>
          }
        />
        <Route
          path="/opportunity-report"
          element={
            <RequireAuth>
              <OpportunityReportPage />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/resume" replace />} />
      </Routes>
    </Shell>
  )
}
