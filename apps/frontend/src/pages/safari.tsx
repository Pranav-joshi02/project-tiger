import React, { useEffect, useState } from "react"
import { api } from "../lib/api"
import { SafariRoute, LiveSafariSighting, SightseeingZone, TigerLocation, CameraStation } from "../lib/types"
import { Card } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Dialog } from "../components/ui/dialog"
import RealPenchMap from "../components/map/real-pench-map"
import SpotTigerModal from "../components/map/spot-tiger-modal"
import {
  Compass,
  MapPin,
  Clock,
  Car,
  Eye,
  Camera,
  Flame,
  Radio,
  Sparkles,
  Search,
  Sunrise,
  Sun,
  Moon,
  ChevronRight,
  PlusCircle,
  CheckCircle,
  AlertTriangle,
  Send,
  Navigation,
  ShieldCheck,
  TrendingUp,
  Layers,
  Crosshair,
  CheckCircle2
} from "lucide-react"

export const SafariPage: React.FC = () => {
  const [routes, setRoutes] = useState<SafariRoute[]>([])
  const [sightings, setSightings] = useState<LiveSafariSighting[]>([])
  const [zones, setZones] = useState<SightseeingZone[]>([])
  const [tigers, setTigers] = useState<TigerLocation[]>([])
  const [stations, setStations] = useState<CameraStation[]>([])
  const [selectedRoute, setSelectedRoute] = useState<SafariRoute | null>(null)
  const [zoneFilter, setZoneFilter] = useState<string>("ALL")
  const [timeFilter, setTimeFilter] = useState<"ALL" | "DAWN" | "DUSK" | "NIGHT">("ALL")
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [loading, setLoading] = useState<boolean>(true)
  const [viewMode, setViewMode] = useState<"ROUTES" | "REAL_MAP">("ROUTES")

  // Spot Tiger Modal State
  const [showSpotModal, setShowSpotModal] = useState<boolean>(false)
  const [spotCoords, setSpotCoords] = useState<{ lat: number; lng: number; nearestLandmark?: string } | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [routesData, sightingsData, zonesData, tigersData, stationsData] = await Promise.all([
        api.getSafariRoutes(),
        api.getLiveSafariSightings(),
        api.getSightseeingZones(),
        api.getTigerLocations(),
        api.getStations()
      ])
      setRoutes(routesData)
      setSightings(sightingsData)
      setZones(zonesData)
      setTigers(tigersData)
      setStations(stationsData)
      if (routesData.length > 0 && !selectedRoute) {
        setSelectedRoute(routesData[0])
      }
    } catch (err) {
      console.error("Failed to load safari intelligence:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSightingPlotted = (result: any) => {
    setToastMessage(`Broadcasted sighting of ${result.sighting.tiger_code} (${result.sighting.tiger_name}) at ${result.sighting.location_name}`)
    api.getLiveSafariSightings().then(setSightings)
    api.getTigerLocations().then(setTigers)
    setTimeout(() => setToastMessage(null), 5000)
  }

  // Filtered Safari Routes
  const filteredRoutes = routes.filter(r => {
    const matchesZone = zoneFilter === "ALL" || r.zone === zoneFilter
    const matchesTime =
      timeFilter === "ALL" ||
      (timeFilter === "DAWN" && (r.slot_recommendation === "DAWN_SAFARI" || r.slot_recommendation === "BOTH")) ||
      (timeFilter === "DUSK" && (r.slot_recommendation === "DUSK_SAFARI" || r.slot_recommendation === "BOTH")) ||
      (timeFilter === "NIGHT" && r.slot_recommendation === "NIGHT_BUFFER")
    const matchesSearch =
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.gate_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.resident_tigers && r.resident_tigers.some(t => t.toLowerCase().includes(searchQuery.toLowerCase())))

    return matchesZone && matchesTime && matchesSearch
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Banner: Gate Statuses & Safari Telemetry Notice */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border border-ink-100 rounded-2xl p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gold-50 border border-gold-400/40 flex items-center justify-center text-gold-400 shadow-sm">
            <Compass size={22} className="animate-spin" style={{ animationDuration: "20s" }} />
          </div>
          <div>
            <h2 className="font-serif font-black text-xl text-ink-900 uppercase tracking-wide flex items-center gap-2">
              Safari Route Intelligence & Visibility Forecast
            </h2>
            <p className="text-xs text-ink-700 font-mono">
              Real Pench Tiger Reserve tracks with AI-forecasted visibility scores and live naturalist radio logs
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {toastMessage && (
            <div className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-3.5 py-1.5 rounded-xl text-xs font-mono animate-fade-in shadow-sm flex items-center gap-1.5">
              <CheckCircle2 size={14} className="text-emerald-600" />
              {toastMessage}
            </div>
          )}

          {/* View Mode Toggle: Routes vs Real GIS Map */}
          <div className="surface-inset p-1 rounded-xl border border-ink-100 flex items-center gap-1 shadow-sm">
            <button
              onClick={() => setViewMode("ROUTES")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                viewMode === "ROUTES" ? "bg-white text-ink-900 shadow border border-ink-100" : "text-ink-500 hover:text-ink-900"
              }`}
            >
              Safari Blueprints
            </button>
            <button
              onClick={() => setViewMode("REAL_MAP")}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                viewMode === "REAL_MAP" ? "bg-white text-ink-900 shadow border border-ink-100" : "text-ink-500 hover:text-ink-900"
              }`}
            >
              GIS Map
            </button>
          </div>

          <Button
            variant="outline"
            onClick={() => {
              setSpotCoords(null)
              setShowSpotModal(true)
            }}
            className="text-xs font-mono uppercase font-bold bg-gold-400 text-white hover:bg-gold-500 shadow-sm border-gold-400 flex items-center gap-1.5"
          >
            <PlusCircle size={14} /> Spot & Plot Tiger
          </Button>
        </div>
      </div>

      {/* Safari Gate Status Ticker */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
        {[
          { gate: "Touria Core Gate", status: "OPEN", vehicles: "27/30", prob: "94%" },
          { gate: "Karmajhiri Gate", status: "OPEN", vehicles: "16/20", prob: "86%" },
          { gate: "Gumtara Core Gate", status: "OPEN", vehicles: "11/16", prob: "82%" },
          { gate: "Khursapar MH Gate", status: "OPEN", vehicles: "14/18", prob: "78%" },
          { gate: "Rukhad Buffer", status: "OPEN", vehicles: "8/12", prob: "68%" },
          { gate: "Jamtara Riverbed", status: "REGULATED", vehicles: "7/10", prob: "74%" }
        ].map((g, idx) => (
          <div
            key={idx}
            className="bg-white border border-ink-100 rounded-xl p-2.5 flex flex-col justify-between shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-ink-700 truncate font-semibold">{g.gate}</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <div className="flex items-end justify-between mt-1.5">
              <span className="text-xs font-mono font-bold text-ink-900">{g.vehicles} Slots</span>
              <span className="text-[11px] font-mono font-bold text-gold-400">{g.prob} Tiger Rate</span>
            </div>
          </div>
        ))}
      </div>

      {/* If Real GIS Map View Mode is active, render full real map */}
      {viewMode === "REAL_MAP" ? (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <h3 className="font-serif font-bold text-lg text-ink-900 flex items-center gap-2">
              <Compass size={18} className="text-gold-400" />
              Pench Safari Tracks & Sightseeing Geometries
            </h3>
            <span className="text-xs font-mono text-ink-700">Click anywhere on the map to log a field sighting</span>
          </div>

          <RealPenchMap
            tigers={tigers}
            zones={zones}
            stations={stations}
            routes={routes}
            onMapClickToSpot={(coords) => {
              setSpotCoords(coords)
              setShowSpotModal(true)
            }}
          />
        </div>
      ) : (
        <>
          {/* Filter and Search Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-3.5 rounded-xl border border-ink-100 shadow-sm">
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
              <span className="text-xs font-mono text-ink-500 font-bold mr-1">Zone:</span>
              {["ALL", "TOURIA", "KARMAJHIRI", "GUMTARA", "KHURSAPAR", "RUKHAD"].map(z => (
                <button
                  key={z}
                  onClick={() => setZoneFilter(z)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
                    zoneFilter === z
                      ? "bg-gold-400 text-white shadow-sm font-bold"
                      : "bg-page-50 text-ink-600 hover:text-ink-900 border border-ink-100"
                  }`}
                >
                  {z}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
                <input
                  type="text"
                  placeholder="Search by route, resident tiger (e.g. Baghira)..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="bg-white text-ink-900 placeholder:text-ink-400 border border-ink-100 rounded-xl pl-9 pr-3 py-2 text-xs focus:outline-none focus:border-gold-400 font-mono w-64 shadow-sm"
                />
              </div>
            </div>
          </div>

          {/* Main Content Layout: Route Cards on Left, Detailed Inspector & Live Sighting Stream on Right */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Safari Routes List (5 Cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-serif font-bold text-base text-ink-900 flex items-center gap-2">
                  <Compass size={17} className="text-gold-400" />
                  High-Visibility Safari Tracks ({filteredRoutes.length})
                </h3>
                <span className="text-[11px] font-mono text-emerald-600">Ranked by AI Sighting Prob.</span>
              </div>

              <div className="space-y-3.5">
                {filteredRoutes.map((route) => {
                  const isSelected = selectedRoute?.id === route.id
                  const isUltra = route.visibility_rating >= 90

                  return (
                    <div
                      key={route.id}
                      onClick={() => setSelectedRoute(route)}
                      className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer relative overflow-hidden ${
                        isSelected
                          ? "bg-page-50 border-gold-400 shadow-md border-l-4"
                          : "bg-white border-ink-100 hover:border-ink-200 shadow-sm"
                      }`}
                    >
                      {/* Route Header */}
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-page-100 text-ink-700 border border-ink-200">
                              {route.code}
                            </span>
                            <span className="text-[10px] font-mono text-ink-500 uppercase">
                              {route.gate_name}
                            </span>
                          </div>
                          <h4 className="font-serif font-bold text-base text-ink-900">{route.name}</h4>
                        </div>

                        {/* Visibility Rating Pill */}
                        <div className="text-right shrink-0">
                          <div className={`px-2.5 py-1 rounded-xl font-mono text-xs font-black shadow-sm border ${
                            isUltra
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : "bg-amber-50 text-amber-700 border-amber-200"
                          }`}>
                            {route.visibility_rating}% VISIBILITY
                          </div>
                        </div>
                      </div>

                      {/* Summary */}
                      <p className="text-xs text-ink-600 line-clamp-2 leading-relaxed mb-3">
                        {route.summary}
                      </p>

                      {/* Resident Tigers Badges */}
                      <div className="flex flex-wrap items-center gap-1.5 mb-3">
                        <span className="text-[10px] font-mono text-ink-500 mr-1">Resident Tigers:</span>
                        {route.resident_tigers && route.resident_tigers.map((rt, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-page-50 border border-ink-100 rounded-md text-[10px] font-mono text-ink-700 font-semibold"
                          >
                            {rt}
                          </span>
                        ))}
                      </div>

                      {/* Route Stats Footer */}
                      <div className="border-t border-ink-100 pt-2.5 flex items-center justify-between text-xs text-ink-500 font-mono">
                        <div className="flex items-center gap-3">
                          <span>{route.distance_km} km</span>
                          <span>•</span>
                          <span>{route.duration_hours} hrs</span>
                          <span>•</span>
                          <span className="text-emerald-600">{route.recent_sightings_count_48h || 4} sightings in 48h</span>
                        </div>

                        <ChevronRight size={16} className={`transition-transform ${isSelected ? "text-gold-400 translate-x-1" : "text-ink-400"}`} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right Column: Selected Route Full Waypoint Blueprint & Live Sighting Log (7 Cols) */}
            <div className="lg:col-span-7 space-y-6">
              {selectedRoute ? (
                <Card className="border border-ink-100 bg-white shadow-md p-6 relative overflow-hidden rounded-xl">
                  {/* Decorative Watermark */}
                  <div className="absolute -right-6 -bottom-6 text-page-100 pointer-events-none">
                    <Compass size={180} />
                  </div>

                  {/* Selected Route Header */}
                  <div className="flex flex-wrap items-start justify-between gap-4 border-b border-ink-100 pb-4 mb-4 relative z-10">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-gold-400 text-white">
                          {selectedRoute.code}
                        </span>
                        <span className="text-xs font-mono text-ink-500">
                          {selectedRoute.zone} ZONE • {selectedRoute.gate_name}
                        </span>
                      </div>
                      <h3 className="font-serif font-black text-2xl text-ink-900">{selectedRoute.name}</h3>
                    </div>

                    <div className="flex flex-col items-end">
                      <span className="text-[10px] font-mono text-ink-500 uppercase">AI Visibility Forecast</span>
                      <span className="text-2xl font-black font-mono text-emerald-600 flex items-center gap-1">
                        <TrendingUp size={20} /> {selectedRoute.visibility_rating}%
                      </span>
                    </div>
                  </div>

                  {/* Highlights & Naturalist Pro-Tips */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 relative z-10">
                    <div className="bg-page-50 p-3.5 rounded-xl border border-ink-100 space-y-2">
                      <h4 className="text-xs font-mono font-bold uppercase text-ink-900 flex items-center gap-1.5">
                        <Sparkles size={13} className="text-gold-400" /> Route Highlights
                      </h4>
                      <ul className="text-xs text-ink-600 space-y-1.5 list-disc list-inside">
                        {selectedRoute.highlights && selectedRoute.highlights.map((h, i) => (
                          <li key={i} className="leading-relaxed">{h}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-page-50 p-3.5 rounded-xl border border-ink-100 space-y-2">
                      <h4 className="text-xs font-mono font-bold uppercase text-ink-900 flex items-center gap-1.5">
                        <Eye size={13} className="text-gold-400" /> Field Naturalist Tip
                      </h4>
                      <p className="text-xs text-ink-600 leading-relaxed italic">
                        "{selectedRoute.naturalist_tips}"
                      </p>
                      <div className="pt-2 border-t border-ink-100 flex items-center justify-between text-[11px] font-mono text-ink-500">
                        <span className="flex items-center gap-1"><Camera size={12} className="text-emerald-600" /> Lens:</span>
                        <span className="text-ink-700">{selectedRoute.suggested_lens}</span>
                      </div>
                    </div>
                  </div>

                  {/* Waypoint Track Blueprint */}
                  <div className="space-y-3 mb-6 relative z-10">
                    <h4 className="text-xs font-mono font-bold uppercase text-ink-700 flex items-center gap-1.5">
                      <Navigation size={13} className="text-gold-400" /> Sequential Waypoint Blueprint
                    </h4>

                    <div className="space-y-2">
                      {selectedRoute.waypoints && selectedRoute.waypoints.map((wp) => (
                        <div
                          key={wp.id}
                          className="flex items-start gap-3 p-3 rounded-xl bg-white border border-ink-100 hover:border-ink-200 transition-colors shadow-sm"
                        >
                          <div className="w-6 h-6 rounded-full bg-page-100 border border-ink-200 flex items-center justify-center font-mono text-[10px] font-bold text-ink-700 shrink-0">
                            {wp.order}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-sm text-ink-900">{wp.name}</span>
                              <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                                wp.tiger_sighting_chance >= 85
                                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                  : wp.tiger_sighting_chance >= 70
                                  ? "bg-amber-50 text-amber-700 border border-amber-200"
                                  : "bg-page-50 text-ink-500 border border-ink-100"
                              }`}>
                                {wp.tiger_sighting_chance}% Tiger Chance
                              </span>
                            </div>
                            <p className="text-xs text-ink-500 mt-0.5">{wp.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Permit Booking & Capacity Bar */}
                  <div className="bg-page-50 p-3 rounded-xl border border-ink-100 flex items-center justify-between text-xs font-mono relative z-10">
                    <div>
                      <span className="text-ink-500 uppercase block text-[10px]">Vehicular Permit Capacity</span>
                      <span className="font-bold text-ink-900">{selectedRoute.current_vehicles_booked} of {selectedRoute.max_vehicles} Gypsy slots allocated for next shift</span>
                    </div>
                    <div className="w-32 bg-ink-100 h-2.5 rounded-full overflow-hidden">
                      <div
                        className="bg-gold-400 h-full rounded-full"
                        style={{ width: `${(selectedRoute.current_vehicles_booked / selectedRoute.max_vehicles) * 100}%` }}
                      />
                    </div>
                  </div>
                </Card>
              ) : (
                <div className="p-12 text-center text-ink-400 font-mono">Select a safari route to view details</div>
              )}

              {/* Live Driver Radio Sighting Feed */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-ink-100 pb-2">
                  <h3 className="font-serif font-bold text-base text-ink-900 flex items-center gap-2">
                    <Radio size={16} className="text-red-500 animate-pulse" />
                    Live Naturalist Radio Stream ({sightings.length} Sightings Today)
                  </h3>
                  <span className="text-[10px] font-mono text-ink-500 uppercase">Auto-updating telemetry feed</span>
                </div>

                <div className="space-y-3 max-h-[380px] overflow-y-auto no-scrollbar">
                  {sightings.map((s) => (
                    <div
                      key={s.id}
                      className="p-3.5 rounded-xl bg-white border border-ink-100 hover:border-ink-200 transition-colors shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-ink-900 px-2 py-0.5 rounded bg-page-50 border border-ink-100">
                            {s.tiger_code} • {s.tiger_name}
                          </span>
                          <span className="text-xs font-semibold text-ink-900">{s.location_name}</span>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono text-ink-500">{s.time_ago}</span>
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase">
                            {s.observed_by.replace("_", " ")}
                          </span>
                        </div>
                      </div>

                      <p className="text-xs text-ink-600 leading-relaxed">{s.behavior}</p>

                      <div className="mt-2 pt-2 border-t border-ink-100 flex items-center justify-between text-[10px] font-mono text-ink-500">
                        <span>Route: {s.route_name}</span>
                        <span className="text-emerald-600 font-bold">{(s.confidence_score * 100).toFixed(0)}% Verification Match</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Spot Tiger Modal */}
      <SpotTigerModal
        isOpen={showSpotModal}
        onClose={() => setShowSpotModal(false)}
        initialCoords={spotCoords}
        tigers={tigers}
        onSightingPlotted={handleSightingPlotted}
      />
    </div>
  )
}

export default SafariPage
