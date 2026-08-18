import React from "react"
import { NavLink } from "react-router-dom"
import { LayoutDashboard, Compass, Eye, ShieldAlert, Database, LogOut, Camera } from "lucide-react"

export const Sidebar: React.FC = () => {
  const links = [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/safari", label: "Safari Routes", icon: Compass },
    { to: "/capture", label: "Live Capture", icon: Camera },
    { to: "/tigers", label: "Tiger Catalogue", icon: Eye },
    { to: "/review", label: "Review Queue", icon: ShieldAlert },
    { to: "/runs", label: "Ingestion Runs", icon: Database },
  ]

  return (
    <aside className="fixed left-0 top-0 h-screen w-[242px] sidebar-surface flex flex-col p-6 z-40 shadow-sidebar">
      {/* Brand */}
      <div className="flex items-center gap-3 mb-10">
        <div className="w-10 h-10 rounded-lg bg-gold-400 flex items-center justify-center shadow-md">
          <span className="font-serif font-bold text-xl text-white">P</span>
        </div>
        <div>
          <h2 className="font-serif font-bold text-base leading-none text-white tracking-wide">PENCH</h2>
          <span className="text-[9px] tracking-[2.2px] text-forest-300 uppercase font-mono block mt-0.5">Tiger Intelligence</span>
        </div>
      </div>

      {/* Reserve info */}
      <div className="text-[11px] leading-relaxed text-forest-300/80 mb-6 px-1">
        <span className="text-[8px] tracking-[1.2px] text-gold-400 font-mono font-bold uppercase block mb-1">Pench Tiger Reserve</span>
        Seoni–Chhindwara, MP. India's premier tiger corridor.
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1">
        {links.map((link) => {
          const Icon = link.icon
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-forest-700/60 text-white font-bold"
                    : "text-forest-200/70 hover:bg-forest-800/40 hover:text-white"
                }`
              }
            >
              <Icon size={17} className="shrink-0" />
              {link.label}
            </NavLink>
          )
        })}
      </nav>

      {/* User */}
      <div className="mt-auto pt-5 border-t border-forest-700/40 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-gold-400 flex items-center justify-center font-bold text-white text-xs">
          RJ
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-white truncate">Riya Joshi</p>
          <p className="text-[10px] text-forest-300/60 truncate">Forest Officer</p>
        </div>
        <button className="text-forest-300/50 hover:text-red-300 transition-colors">
          <LogOut size={15} />
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
