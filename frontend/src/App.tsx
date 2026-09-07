import { NavLink, Route, Routes } from 'react-router-dom'
import { NewClaimPage } from './pages/NewClaimPage'
import { ClaimHistoryPage } from './pages/ClaimHistoryPage'

export function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="border-b bg-white px-4 py-4 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-3xl gap-6 text-sm font-medium">
          <NavLink
            to="/"
            end
            className={({ isActive }) => (isActive ? 'text-slate-900 underline' : 'text-slate-500')}
          >
            New Claim
          </NavLink>
          <NavLink
            to="/history"
            className={({ isActive }) => (isActive ? 'text-slate-900 underline' : 'text-slate-500')}
          >
            Claim History
          </NavLink>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<NewClaimPage />} />
        <Route path="/history" element={<ClaimHistoryPage />} />
      </Routes>
    </div>
  )
}
