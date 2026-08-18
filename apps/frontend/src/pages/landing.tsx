import React from "react"
import { useNavigate } from "react-router-dom"
import { ArrowRight, Eye, ShieldAlert, Compass } from "lucide-react"
import { Button } from "../components/ui/button"

export const LandingPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div 
      className="relative min-h-screen w-full flex flex-col justify-between p-8 bg-cover bg-center select-none"
      style={{ backgroundImage: "url('/assets/images/pench_forest_godrays.jpg')" }}
    >
      {/* Light overlay gradient for clean professional look */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/90 via-white/70 to-white/90 pointer-events-none" />

      {/* Header Overlay */}
      <header className="relative z-10 flex items-center justify-between w-full max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-md bg-gold-400 flex items-center justify-center shadow-lg">
            <span className="font-serif font-black text-lg text-white">P</span>
          </div>
          <span className="font-serif font-bold text-ink-900 tracking-wider text-sm">PENCH TIGER RESERVE</span>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-xs font-semibold tracking-widest text-ink-600 uppercase font-mono">
          <button onClick={() => navigate("/dashboard")} className="hover:text-gold-400 transition-colors">
            Real GIS Telemetry
          </button>
          <button onClick={() => navigate("/safari")} className="hover:text-gold-400 transition-colors flex items-center gap-1">
            <Compass size={13} /> Safari Routes
          </button>
          <button onClick={() => navigate("/tigers")} className="hover:text-gold-400 transition-colors">
            Tiger Catalogue
          </button>
        </nav>

        <Button variant="outline" className="text-xs uppercase px-4 py-2 border-gold-400 text-gold-400 hover:bg-gold-50" onClick={() => navigate("/dashboard")}>
          Access System
        </Button>
      </header>

      {/* Center Block */}
      <main className="relative z-10 flex flex-col items-center text-center my-auto max-w-4xl mx-auto animate-fade-in">
        <span className="text-xs md:text-sm font-semibold tracking-[0.35em] text-gold-400 uppercase mb-4 font-mono flex items-center gap-2">
          Surveillance & Spatial AI Platform
        </span>
        
        <h1 className="text-5xl md:text-8xl font-black tracking-tight text-ink-900 uppercase font-serif mb-6 leading-none">
          LET'S SAVE ALL OF <br />
          <span className="text-gold-400">TIGER</span>
        </h1>

        <p className="text-sm md:text-base text-ink-600 max-w-xl leading-relaxed mb-8">
          Real-time GIS telemetry mapping, PostGIS spatial route intelligence, pgvector Re-ID matching, and field tiger spotting across Pench National Park.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <Button variant="primary" className="px-8 py-4 gap-2 text-sm uppercase tracking-wider bg-forest-800 text-white font-bold shadow-xl" onClick={() => navigate("/dashboard")}>
            Launch GIS Dashboard <ArrowRight size={16} />
          </Button>
          <Button variant="secondary" className="px-8 py-4 gap-2 text-sm uppercase tracking-wider bg-gold-400 text-white shadow-xl" onClick={() => navigate("/safari")}>
            <Compass size={16} /> Safari Route Intelligence
          </Button>
          <Button variant="outline" className="px-8 py-4 gap-2 text-sm uppercase tracking-wider border-ink-200 text-ink-900 bg-white shadow-sm" onClick={() => navigate("/review")}>
            Review Queue <ShieldAlert size={16} />
          </Button>
        </div>
      </main>

      {/* Footer Block */}
      <footer className="relative z-10 flex flex-col md:flex-row items-center justify-between w-full max-w-7xl mx-auto border-t border-ink-200 pt-6 text-xs text-ink-500">
        <p className="max-w-md text-center md:text-left leading-relaxed">
          Pench Tiger Reserve spatial intelligence and automated individual re-identification system.
        </p>
        <span className="font-mono tracking-widest uppercase mt-4 md:mt-0 text-gold-400">
          GIS TELEMETRY NODE // ACTIVE
        </span>
      </footer>
    </div>
  )
}

export default LandingPage
