import React from "react"
import { Routes, Route, Navigate, useLocation } from "react-router-dom"
import { Sidebar } from "./components/layout/sidebar"
import { LandingPage } from "./pages/landing"
import { DashboardPage } from "./pages/dashboard"
import { SafariPage } from "./pages/safari"
import { ReviewPage } from "./pages/review"
import { TigersPage } from "./pages/tigers"
import { CapturePage } from "./pages/capture"

export const App: React.FC = () => {
  const location = useLocation()
  const isLanding = location.pathname === "/"

  return (
    <div className="relative min-h-screen bg-page-100 text-ink-900">
      {isLanding ? (
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      ) : (
        <div className="flex">
          <Sidebar />
          
          <main className="ml-[242px] flex-1 min-h-screen p-8 bg-page-100 no-scrollbar overflow-x-hidden">
            <header className="flex items-center justify-between border-b border-ink-100 pb-4 mb-6">
              <div>
                <h1 className="font-serif font-bold text-2xl text-ink-900 tracking-tight">PTR Surveillance</h1>
                <p className="text-[10px] text-ink-400 font-mono tracking-widest uppercase mt-0.5">Pench Sanctuary Telemetry Node</p>
              </div>
              <div className="text-xs text-ink-400 font-mono flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-forest-400 inline-block"></span>
                NODE ACTIVE &middot; {new Date().toLocaleDateString()}
              </div>
            </header>
            
            <Routes>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/safari" element={<SafariPage />} />
              <Route path="/review" element={<ReviewPage />} />
              <Route path="/tigers" element={<TigersPage />} />
              <Route path="/capture" element={<CapturePage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      )}
    </div>
  )
}

export default App
