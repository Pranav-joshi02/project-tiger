import React, { useState, useRef, useEffect } from "react"
import {
  TigerLocation,
  SightseeingZone,
  CameraStation,
  SafariRoute
} from "../../lib/types"
import {
  Eye,
  Camera,
  Compass,
  Layers,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sun,
  Sunrise,
  Moon,
  MapPin,
  Flame,
  Activity,
  Maximize2,
  X,
  Sparkles,
  Info,
  Navigation,
  CheckCircle2,
  AlertCircle,
  Radio
} from "lucide-react"
import ThreeMap from "../ThreeMap"

interface InteractiveMapProps {
  tigers?: TigerLocation[]
  zones?: SightseeingZone[]
  stations?: CameraStation[]
  routes?: SafariRoute[]
  selectedTigerId?: string | null
  selectedStationCode?: string | null
  focusedLocation?: { lat: number; lng: number; label?: string } | null
  onSelectTiger?: (tiger: TigerLocation | null) => void
  onSelectZone?: (zone: SightseeingZone | null) => void
  onSelectStation?: (station: CameraStation | null) => void
  onNavigateToSafari?: (routeCode?: string) => void
}

export const InteractiveReserveMap: React.FC<InteractiveMapProps> = ({
  tigers = [],
  zones = [],
  stations = [],
  routes = [],
  selectedTigerId,
  selectedStationCode,
  focusedLocation,
  onSelectTiger,
  onSelectZone,
  onSelectStation,
  onNavigateToSafari
}) => {
  // Map View Mode: 2D Tactical Vector Map vs 3D Holographic View
  const [viewMode, setViewMode] = useState<"2D" | "3D">("2D")

  // Layer Toggles
  const [showTigers, setShowTigers] = useState<boolean>(true)
  const [showZones, setShowZones] = useState<boolean>(true)
  const [showStations, setShowStations] = useState<boolean>(true)
  const [showRoutes, setShowRoutes] = useState<boolean>(true)
  const [showHeatmap, setShowHeatmap] = useState<boolean>(true)

  // Time-of-Day Filter (Simulates dynamic sighting visibility shifts)
  const [timeSlot, setTimeSlot] = useState<"MORNING" | "AFTERNOON" | "NIGHT">("MORNING")

  // Map Navigation State (Pan & Zoom)
  const [zoom, setZoom] = useState<number>(1)
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState<boolean>(false)
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [cursorGeo, setCursorGeo] = useState<{ lat: number; lng: number }>({ lat: 22.7350, lng: 79.3080 })

  // Active Selected Inspection Card
  const [activeTiger, setActiveTiger] = useState<TigerLocation | null>(null)
  const [activeZone, setActiveZone] = useState<SightseeingZone | null>(null)
  const [activeStation, setActiveStation] = useState<CameraStation | null>(null)

  const mapContainerRef = useRef<HTMLDivElement>(null)

  // Bounding coordinate extent for Pench Reserve viewport
  const MIN_LAT = 22.6450
  const MAX_LAT = 22.7850
  const MIN_LNG = 79.2450
  const MAX_LNG = 79.3750

  // Coordinate Projection to SVG Canvas (0 to 1000 x, 0 to 700 y)
  const projectCoords = (lat: number, lng: number) => {
    const x = ((lng - MIN_LNG) / (MAX_LNG - MIN_LNG)) * 1000
    const y = ((MAX_LAT - lat) / (MAX_LAT - MIN_LAT)) * 700
    return { x, y }
  }

  // Handle external focus (e.g. when an alert "Locate on Map" is clicked)
  useEffect(() => {
    if (focusedLocation) {
      const { x, y } = projectCoords(focusedLocation.lat, focusedLocation.lng)
      // Center the map around this point
      const centerX = 500
      const centerY = 350
      setPan({
        x: (centerX - x) * 1.4,
        y: (centerY - y) * 1.4
      })
      setZoom(1.4)
    }
  }, [focusedLocation])

  // Mouse pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    // Only drag if left click and not interacting with controls
    if (e.button !== 0) return
    setIsDragging(true)
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (mapContainerRef.current) {
      const rect = mapContainerRef.current.getBoundingClientRect()
      const relX = (e.clientX - rect.left - pan.x) / (rect.width * zoom)
      const relY = (e.clientY - rect.top - pan.y) / (rect.height * zoom)
      const lat = MAX_LAT - relY * (MAX_LAT - MIN_LAT)
      const lng = MIN_LNG + relX * (MAX_LNG - MIN_LNG)
      setCursorGeo({
        lat: Math.max(MIN_LAT, Math.min(MAX_LAT, lat)),
        lng: Math.max(MIN_LNG, Math.min(MAX_LNG, lng))
      })
    }

    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 2.8))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.75))
  const handleReset = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setActiveTiger(null)
    setActiveZone(null)
    setActiveStation(null)
  }

  // Get current visibility score based on selected time slot
  const getZoneScore = (zone: SightseeingZone) => {
    if (timeSlot === "MORNING") return zone.visibility_score_morning
    if (timeSlot === "AFTERNOON") return zone.visibility_score_afternoon
    return zone.visibility_score_night
  }

  return (
    <div className="relative w-full h-[580px] rounded-2xl overflow-hidden border border-forest-500/30 bg-forest-950/90 shadow-2xl flex flex-col select-none">
      {/* Top Floating Controls Bar */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Left: Pench Core Telemetry Status & 2D/3D Switcher */}
        <div className="flex items-center gap-2 pointer-events-auto">
          <div className="glass-dark px-3.5 py-2 rounded-xl border border-forest-500/30 flex items-center gap-2.5 shadow-lg backdrop-blur-md">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
            <div>
              <h3 className="font-serif font-black text-xs text-gold-gradient leading-none">PENCH SPATIAL TELEMETRY</h3>
              <p className="text-[9px] font-mono text-slate-400 leading-tight mt-0.5">
                {tigers.length} Tigers Active • {zones.length} Hotspots Mapped
              </p>
            </div>
          </div>

          <div className="glass-dark p-1 rounded-xl border border-forest-500/30 flex items-center gap-1 shadow-lg">
            <button
              onClick={() => setViewMode("2D")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                viewMode === "2D"
                  ? "bg-luxe-gold text-forest-950 shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              2D Tactical
            </button>
            <button
              onClick={() => setViewMode("3D")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                viewMode === "3D"
                  ? "bg-luxe-gold text-forest-950 shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              3D Hologram
            </button>
          </div>
        </div>

        {/* Center: Time-of-Day Sighting Filter */}
        <div className="glass-dark p-1 rounded-xl border border-forest-500/30 flex items-center gap-1 shadow-lg pointer-events-auto">
          <button
            onClick={() => setTimeSlot("MORNING")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              timeSlot === "MORNING"
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sunrise size={13} className="text-amber-400" />
            <span>Dawn (06:00-09:30)</span>
          </button>

          <button
            onClick={() => setTimeSlot("AFTERNOON")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              timeSlot === "AFTERNOON"
                ? "bg-orange-500/20 text-orange-300 border border-orange-500/40 font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sun size={13} className="text-orange-400" />
            <span>Dusk (15:30-18:30)</span>
          </button>

          <button
            onClick={() => setTimeSlot("NIGHT")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              timeSlot === "NIGHT"
                ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 font-bold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Moon size={13} className="text-indigo-400" />
            <span>Night Buffer</span>
          </button>
        </div>

        {/* Right: Layer Selector & Zoom Controls */}
        <div className="flex items-center gap-2 pointer-events-auto">
          {/* Zoom Buttons */}
          <div className="glass-dark p-1 rounded-xl border border-forest-500/30 flex items-center gap-1 shadow-lg">
            <button
              onClick={handleZoomIn}
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-forest-800/60 transition-colors"
              title="Zoom In"
            >
              <ZoomIn size={15} />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-forest-800/60 transition-colors"
              title="Zoom Out"
            >
              <ZoomOut size={15} />
            </button>
            <button
              onClick={handleReset}
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-forest-800/60 transition-colors"
              title="Reset View"
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Map Viewport */}
      {viewMode === "3D" ? (
        <div className="w-full h-full">
          <ThreeMap
            points={[
              ...stations.map(s => ({ id: s.code, lat: s.latitude, lng: s.longitude, type: "station" as const, label: s.name })),
              ...tigers.map(t => ({ id: t.code, lat: t.latitude, lng: t.longitude, type: "tiger" as const, label: `${t.code} ${t.name}` }))
            ]}
          />
        </div>
      ) : (
        <div
          ref={mapContainerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="relative w-full h-full overflow-hidden cursor-crosshair bg-[#061710]"
          style={{ touchAction: "none" }}
        >
          {/* SVG Map Canvas */}
          <svg
            viewBox="0 0 1000 700"
            className="w-full h-full transition-transform duration-75 origin-center"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: "center center"
            }}
          >
            <defs>
              {/* Radial Gradients for Sighting Probability Zones */}
              <radialGradient id="highProbGrad" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#e5a44d" stopOpacity="0.45" />
                <stop offset="60%" stopColor="#e5a44d" stopOpacity="0.18" />
                <stop offset="100%" stopColor="#e5a44d" stopOpacity="0" />
              </radialGradient>

              <radialGradient id="ultraProbGrad" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.45" />
                <stop offset="60%" stopColor="#10b981" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
              </radialGradient>

              <radialGradient id="waterbodyGrad" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.35" />
                <stop offset="70%" stopColor="#0284c7" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#0369a1" stopOpacity="0" />
              </radialGradient>

              <filter id="glowEffect" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Background Reserve Topography & Terrain Contours */}
            <rect width="1000" height="700" fill="#081c15" />

            {/* Grid Lines */}
            <g stroke="#1b4332" strokeWidth="0.5" opacity="0.35">
              {[100, 200, 300, 400, 500, 600, 700, 800, 900].map(x => (
                <line key={`gx-${x}`} x1={x} y1="0" x2={x} y2="700" />
              ))}
              {[100, 200, 300, 400, 500, 600].map(y => (
                <line key={`gy-${y}`} x1="0" y1={y} x2="1000" y2={y} />
              ))}
            </g>

            {/* Pench River / Reservoir Waterbody Features */}
            <path
              d="M 120,40 Q 220,120 340,160 T 520,240 T 680,260 T 880,320 T 960,420"
              fill="none"
              stroke="#0369a1"
              strokeWidth="18"
              strokeLinecap="round"
              opacity="0.4"
            />
            <path
              d="M 120,40 Q 220,120 340,160 T 520,240 T 680,260 T 880,320 T 960,420"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="4"
              strokeLinecap="round"
              opacity="0.8"
            />

            {/* Totladoh Reservoir Lake Body */}
            <path
              d="M 280,100 C 350,80 440,120 460,190 C 480,260 410,310 320,280 C 240,250 220,130 280,100 Z"
              fill="#0369a1"
              opacity="0.25"
              stroke="#38bdf8"
              strokeWidth="1.5"
              strokeDasharray="4 3"
            />
            <text x="320" y="180" fill="#7dd3fc" fontSize="10" fontFamily="DM Mono" letterSpacing="1" opacity="0.6">
              TOTLADOH WATER BASIN
            </text>

            {/* Bodhanala Waterbody */}
            <ellipse cx="450" cy="360" rx="45" ry="30" fill="url(#waterbodyGrad)" stroke="#38bdf8" strokeWidth="1.5" />
            <text x="450" y="365" textAnchor="middle" fill="#bae6fd" fontSize="9" fontFamily="DM Mono" opacity="0.8">
              Bodhanala
            </text>

            {/* Pench National Park Core Boundary Line */}
            <path
              d="M 160,80 C 380,40 720,60 880,130 C 950,220 940,460 880,580 C 760,660 380,670 200,600 C 100,480 90,200 160,80 Z"
              fill="#1b4332"
              fillOpacity="0.12"
              stroke="#e5a44d"
              strokeWidth="1.5"
              strokeDasharray="6 4"
              opacity="0.6"
            />
            <text x="180" y="110" fill="#e5a44d" fontSize="11" fontFamily="Playfair Display" fontWeight="bold" opacity="0.7">
              PENCH NATIONAL PARK · CORE SECTOR
            </text>

            {/* LAYER: Safari Tracks */}
            {showRoutes && (
              <g id="safari-routes">
                {/* Touria Circuit (Route A) */}
                <path
                  d="M 500,530 Q 520,440 590,300 Q 560,260 450,360 Q 480,470 500,530"
                  fill="none"
                  stroke="#fbbf24"
                  strokeWidth="2.5"
                  strokeDasharray="5 3"
                  opacity="0.8"
                />
                {/* Karmajhiri Trail (Route B) */}
                <path
                  d="M 330,590 Q 340,450 320,280 Q 300,180 340,160"
                  fill="none"
                  stroke="#34d399"
                  strokeWidth="2"
                  strokeDasharray="4 3"
                  opacity="0.75"
                />
                {/* Gumtara Loop (Route C) */}
                <path
                  d="M 160,490 Q 200,430 250,450 Q 280,480 220,530 Z"
                  fill="none"
                  stroke="#a78bfa"
                  strokeWidth="2"
                  strokeDasharray="4 3"
                  opacity="0.75"
                />
              </g>
            )}

            {/* LAYER: Tentative Sightseeing Zones (High & Medium Visibility Areas) */}
            {showZones && (
              <g id="sightseeing-zones">
                {zones.map((zone) => {
                  const { x, y } = projectCoords(zone.latitude, zone.longitude)
                  const score = getZoneScore(zone)
                  const isUltra = score >= 90
                  const isHigh = score >= 80 && score < 90
                  const radius = (zone.radius_meters / 1000) * 80

                  const isSelected = activeZone?.id === zone.id

                  return (
                    <g
                      key={zone.id}
                      className="cursor-pointer group"
                      onClick={() => {
                        setActiveZone(zone)
                        setActiveTiger(null)
                        setActiveStation(null)
                        if (onSelectZone) onSelectZone(zone)
                      }}
                    >
                      {/* Translucent Probability Halo */}
                      <circle
                        cx={x}
                        cy={y}
                        r={radius}
                        fill={isUltra ? "url(#ultraProbGrad)" : "url(#highProbGrad)"}
                        stroke={isUltra ? "#34d399" : "#e5a44d"}
                        strokeWidth={isSelected ? "3" : "1.2"}
                        strokeDasharray={isSelected ? "none" : "4 3"}
                        className="transition-all duration-300 group-hover:stroke-width-3"
                      />

                      {/* Zone Center Pulsing Radar Ring */}
                      <circle
                        cx={x}
                        cy={y}
                        r={12}
                        fill={isUltra ? "#059669" : "#d97706"}
                        fillOpacity="0.25"
                        stroke={isUltra ? "#34d399" : "#fbbf24"}
                        strokeWidth="1.5"
                      />

                      {/* Hotspot Target Cross */}
                      <line x1={x - 6} y1={y} x2={x + 6} y2={y} stroke="#fff" strokeWidth="1" opacity="0.8" />
                      <line x1={x} y1={y - 6} x2={x} y2={y + 6} stroke="#fff" strokeWidth="1" opacity="0.8" />

                      {/* Floating Badge Label */}
                      <g transform={`translate(${x}, ${y - radius - 8})`}>
                        <rect
                          x="-65"
                          y="-18"
                          width="130"
                          height="20"
                          rx="5"
                          fill="#081c15"
                          fillOpacity="0.9"
                          stroke={isUltra ? "#34d399" : "#e5a44d"}
                          strokeWidth="1"
                        />
                        <text
                          x="0"
                          y="-5"
                          textAnchor="middle"
                          fill={isUltra ? "#6ee7b7" : "#fde68a"}
                          fontSize="9"
                          fontFamily="DM Mono"
                          fontWeight="bold"
                        >
                          {score}% · {zone.name.split(" ")[0]}
                        </text>
                      </g>
                    </g>
                  )
                })}
              </g>
            )}

            {/* LAYER: Camera Stations */}
            {showStations && (
              <g id="camera-stations">
                {stations.map((stn) => {
                  const { x, y } = projectCoords(stn.latitude, stn.longitude)
                  const isSelected = activeStation?.code === stn.code || selectedStationCode === stn.code

                  return (
                    <g
                      key={stn.code}
                      className="cursor-pointer group"
                      onClick={() => {
                        setActiveStation(stn)
                        setActiveTiger(null)
                        setActiveZone(null)
                        if (onSelectStation) onSelectStation(stn)
                      }}
                    >
                      {/* Pin Circle */}
                      <circle
                        cx={x}
                        cy={y}
                        r={isSelected ? "7" : "5"}
                        fill="#10b981"
                        stroke="#fff"
                        strokeWidth={isSelected ? "2" : "1"}
                        className="transition-all"
                      />
                      {/* Station Code Text */}
                      <text
                        x={x + 8}
                        y={y + 3}
                        fill="#a7f3d0"
                        fontSize="8"
                        fontFamily="DM Mono"
                        fontWeight="600"
                      >
                        {stn.code}
                      </text>
                    </g>
                  )
                })}
              </g>
            )}

            {/* LAYER: Approximate Tiger Locations */}
            {showTigers && (
              <g id="tiger-markers">
                {tigers.map((tiger) => {
                  const { x, y } = projectCoords(tiger.latitude, tiger.longitude)
                  const isSelected = activeTiger?.id === tiger.id || selectedTigerId === tiger.id

                  return (
                    <g
                      key={tiger.id}
                      className="cursor-pointer group"
                      onClick={() => {
                        setActiveTiger(tiger)
                        setActiveZone(null)
                        setActiveStation(null)
                        if (onSelectTiger) onSelectTiger(tiger)
                      }}
                    >
                      {/* Movement trail line if available */}
                      {tiger.recent_coordinates && tiger.recent_coordinates.length > 1 && (
                        <polyline
                          points={tiger.recent_coordinates
                            .map(c => {
                              const p = projectCoords(c.lat, c.lng)
                              return `${p.x},${p.y}`
                            })
                            .join(" ")}
                          fill="none"
                          stroke="#e5a44d"
                          strokeWidth="1.5"
                          strokeDasharray="3 2"
                          opacity="0.6"
                        />
                      )}

                      {/* Pulsing Animated Radar Ring */}
                      <circle
                        cx={x}
                        cy={y}
                        r={isSelected ? "24" : "16"}
                        fill="none"
                        stroke="#e5a44d"
                        strokeWidth="1.5"
                        opacity="0.7"
                        className="animate-ping"
                        style={{ transformOrigin: `${x}px ${y}px`, animationDuration: "2.4s" }}
                      />

                      {/* Glowing Diamond Tiger Badge */}
                      <polygon
                        points={`${x},${y - 12} ${x + 12},${y} ${x},${y + 12} ${x - 12},${y}`}
                        fill="#d97706"
                        stroke="#fef3c7"
                        strokeWidth={isSelected ? "2.5" : "1.5"}
                        filter="url(#glowEffect)"
                        className="transition-transform group-hover:scale-125 origin-center"
                      />

                      {/* Tiger Icon / Monogram */}
                      <text
                        x={x}
                        y={y + 3}
                        textAnchor="middle"
                        fill="#081c15"
                        fontSize="9"
                        fontFamily="DM Mono"
                        fontWeight="black"
                      >
                        🐅
                      </text>

                      {/* Floating Moniker Pill */}
                      <g transform={`translate(${x}, ${y + 22})`}>
                        <rect
                          x="-45"
                          y="-8"
                          width="90"
                          height="16"
                          rx="8"
                          fill="#183d31"
                          stroke="#e5a44d"
                          strokeWidth="1"
                        />
                        <text
                          x="0"
                          y="3"
                          textAnchor="middle"
                          fill="#fef3c7"
                          fontSize="8.5"
                          fontFamily="DM Mono"
                          fontWeight="bold"
                        >
                          {tiger.code} • {tiger.name}
                        </text>
                      </g>
                    </g>
                  )
                })}
              </g>
            )}

            {/* Highlight Crosshair for Focused Alerts */}
            {focusedLocation && (
              <g transform={`translate(${projectCoords(focusedLocation.lat, focusedLocation.lng).x}, ${projectCoords(focusedLocation.lat, focusedLocation.lng).y})`}>
                <circle r="30" fill="none" stroke="#ef4444" strokeWidth="2" className="animate-ping" />
                <circle r="14" fill="#ef4444" fillOpacity="0.3" stroke="#ef4444" strokeWidth="2" />
                <line x1="-20" y1="0" x2="20" y2="0" stroke="#ef4444" strokeWidth="2" />
                <line x1="0" y1="-20" x2="0" y2="20" stroke="#ef4444" strokeWidth="2" />
                <text x="0" y="-18" textAnchor="middle" fill="#fca5a5" fontSize="10" fontFamily="DM Mono" fontWeight="bold">
                  {focusedLocation.label || "ALERT INCIDENT TARGET"}
                </text>
              </g>
            )}
          </svg>

          {/* Bottom Left HUD: Coordinates & Scale */}
          <div className="absolute bottom-4 left-4 z-10 glass-dark px-3 py-2 rounded-xl border border-forest-500/30 flex items-center gap-3 text-[10px] font-mono text-slate-300 pointer-events-none">
            <div className="flex items-center gap-1.5">
              <Navigation size={12} className="text-luxe-gold rotate-45" />
              <span>{cursorGeo.lat.toFixed(4)}° N, {cursorGeo.lng.toFixed(4)}° E</span>
            </div>
            <div className="w-px h-3 bg-forest-500/40" />
            <span className="text-emerald-400">ELEV: 380m ASL</span>
            <div className="w-px h-3 bg-forest-500/40" />
            <span className="text-amber-400 font-bold">ZOOM: {zoom.toFixed(2)}x</span>
          </div>

          {/* Bottom Right Layer Legend */}
          <div className="absolute bottom-4 right-4 z-10 glass-dark p-2.5 rounded-xl border border-forest-500/30 flex items-center gap-3 text-xs font-mono text-slate-300">
            <button
              onClick={() => setShowTigers(!showTigers)}
              className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
                showTigers ? "bg-amber-500/20 text-amber-300" : "text-slate-500 line-through"
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-sm bg-luxe-gold" />
              <span>Tigers ({tigers.length})</span>
            </button>

            <button
              onClick={() => setShowZones(!showZones)}
              className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
                showZones ? "bg-emerald-500/20 text-emerald-300" : "text-slate-500 line-through"
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full border border-emerald-400" />
              <span>Sightseeing ({zones.length})</span>
            </button>

            <button
              onClick={() => setShowStations(!showStations)}
              className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
                showStations ? "bg-blue-500/20 text-blue-300" : "text-slate-500 line-through"
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              <span>Stations ({stations.length})</span>
            </button>

            <button
              onClick={() => setShowRoutes(!showRoutes)}
              className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
                showRoutes ? "bg-yellow-500/20 text-yellow-300" : "text-slate-500 line-through"
              }`}
            >
              <span className="w-3 border-t-2 border-dashed border-yellow-400" />
              <span>Safari Tracks</span>
            </button>
          </div>
        </div>
      )}

      {/* Slide-in Telemetry Inspection Drawer (Tiger / Zone / Station) */}
      {(activeTiger || activeZone || activeStation) && (
        <div className="absolute top-16 right-4 z-30 w-80 glass-dark rounded-2xl border border-forest-500/40 p-4 shadow-2xl animate-fade-in backdrop-blur-xl max-h-[460px] overflow-y-auto no-scrollbar">
          {/* Header with Close */}
          <div className="flex items-center justify-between border-b border-forest-500/20 pb-2.5 mb-3">
            <span className="text-[10px] font-mono text-luxe-gold tracking-wider uppercase font-bold flex items-center gap-1.5">
              <Sparkles size={12} />
              {activeTiger ? "Tiger Telemetry Profile" : activeZone ? "Sightseeing Hotspot" : "Camera Station"}
            </span>
            <button
              onClick={() => {
                setActiveTiger(null)
                setActiveZone(null)
                setActiveStation(null)
              }}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          {/* Tiger Selected State */}
          {activeTiger && (
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-amber-950/80 border border-amber-600/40 flex items-center justify-center text-2xl shadow-lg">
                  🐅
                </div>
                <div>
                  <h4 className="font-serif font-bold text-lg text-white leading-tight">
                    {activeTiger.name} ({activeTiger.code})
                  </h4>
                  <p className="text-[11px] font-mono text-slate-400">
                    {activeTiger.sex} • {activeTiger.approx_zone}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs bg-forest-900/80 p-2.5 rounded-xl border border-forest-500/20">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">Current Activity</span>
                  <span className="font-bold text-emerald-400">{activeTiger.current_activity.replace("_", " ")}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">Last Verified</span>
                  <span className="font-bold text-luxe-gold">{activeTiger.last_seen_relative}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">Confidence</span>
                  <span className="font-mono text-white font-semibold">{(activeTiger.sighting_confidence * 100).toFixed(0)}% Match</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">Territory Size</span>
                  <span className="font-mono text-white font-semibold">{activeTiger.territory_radius_km} km²</span>
                </div>
              </div>

              <div className="text-xs text-slate-300 bg-forest-900/60 p-2.5 rounded-xl border border-forest-500/20">
                <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">Recommended Safari Slot</span>
                <p className="font-semibold text-amber-300">{activeTiger.recommended_time_slot}</p>
                <p className="text-[11px] text-slate-400 mt-1">{activeTiger.notes}</p>
              </div>

              {onNavigateToSafari && (
                <button
                  onClick={() => onNavigateToSafari("PTR-SR-01")}
                  className="w-full py-2 bg-luxe-gold hover:bg-yellow-500 text-forest-950 text-xs font-mono font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-lg transition-all"
                >
                  <Compass size={14} /> View Safari Routes for {activeTiger.name}
                </button>
              )}
            </div>
          )}

          {/* Sightseeing Zone Selected State */}
          {activeZone && (
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-700/50">
                    {activeZone.zone_type} ZONE
                  </span>
                  <span className="font-mono font-bold text-sm text-luxe-gold">
                    {getZoneScore(activeZone)}% Visibility
                  </span>
                </div>
                <h4 className="font-serif font-bold text-lg text-white mt-1">{activeZone.name}</h4>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">{activeZone.description}</p>
              </div>

              {/* Visibility Comparison Breakdown */}
              <div className="bg-forest-900/80 p-3 rounded-xl border border-forest-500/20 space-y-2">
                <span className="text-[10px] font-mono text-slate-400 uppercase block">Time-of-Day Visibility Rating</span>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300 flex items-center gap-1"><Sunrise size={11} className="text-amber-400" /> Morning Safari:</span>
                    <span className="font-mono font-bold text-amber-300">{activeZone.visibility_score_morning}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300 flex items-center gap-1"><Sun size={11} className="text-orange-400" /> Afternoon Safari:</span>
                    <span className="font-mono font-bold text-orange-300">{activeZone.visibility_score_afternoon}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-300 flex items-center gap-1"><Moon size={11} className="text-indigo-400" /> Night Buffer:</span>
                    <span className="font-mono font-bold text-indigo-300">{activeZone.visibility_score_night}%</span>
                  </div>
                </div>
              </div>

              {/* Resident Tigers Frequent in Zone */}
              <div className="bg-forest-900/60 p-2.5 rounded-xl border border-forest-500/20 text-xs">
                <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">Resident Tigers Active Here</span>
                <div className="space-y-1">
                  {activeZone.resident_tigers.map(rt => (
                    <div key={rt.code} className="flex justify-between text-[11px]">
                      <span className="text-white font-semibold">{rt.name} ({rt.code})</span>
                      <span className="text-emerald-400 font-mono">{rt.likelihood}% Probability</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-[11px] text-slate-400 font-mono">
                <p><strong>Recommended Gate:</strong> {activeZone.recommended_gate}</p>
                <p className="mt-0.5"><strong>Best Timing:</strong> {activeZone.best_safari_timing}</p>
              </div>
            </div>
          )}

          {/* Camera Station Selected State */}
          {activeStation && (
            <div className="space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-serif font-bold text-lg text-white">{activeStation.name}</h4>
                  <p className="text-xs font-mono text-emerald-400 font-semibold">{activeStation.code} • {activeStation.zone} ZONE</p>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-700/50">
                  {activeStation.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs bg-forest-900/80 p-2.5 rounded-xl border border-forest-500/20">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">Coordinates</span>
                  <span className="font-mono text-white text-[11px]">{activeStation.latitude.toFixed(4)}° N, {activeStation.longitude.toFixed(4)}° E</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">Telemetry Check</span>
                  <span className="font-mono text-slate-200 text-[11px]">{activeStation.last_check || "Active Online"}</span>
                </div>
              </div>

              <div className="bg-forest-900/60 p-2.5 rounded-xl border border-forest-500/20 text-xs">
                <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">Station Telemetry Status</span>
                <p className="text-slate-300">Dual-lens PIR sensor operating nominally with 4G LoRa mesh link to Pench central telemetry node.</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default InteractiveReserveMap
