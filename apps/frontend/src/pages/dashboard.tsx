import React, { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  ShieldAlert,
  Compass,
  Eye,
  Database,
  Activity,
  AlertTriangle,
  Flame,
  Radio,
  Sparkles,
  MapPin,
  CheckCircle2,
  AlertCircle,
  Filter,
  Plus,
  Crosshair,
  ExternalLink,
  ChevronRight,
  RefreshCw,
  Bell,
  PlusCircle,
  Send
} from "lucide-react"
import { api } from "../lib/api"
import {
  DashboardData,
  CameraStation,
  TigerLocation,
  SightseeingZone,
  SafariRoute,
  Alert
} from "../lib/types"
import { Card } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Dialog } from "../components/ui/dialog"
import RealPenchMap from "../components/map/real-pench-map"
import SpotTigerModal from "../components/map/spot-tiger-modal"
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer } from "recharts"

const chartData = [
  { name: "June", images: 41208, tigers: 201 },
  { name: "July", images: 32981, tigers: 147 },
  { name: "August", images: 38472, tigers: 184 },
]

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [stations, setStations] = useState<CameraStation[]>([])
  const [tigers, setTigers] = useState<TigerLocation[]>([])
  const [zones, setZones] = useState<SightseeingZone[]>([])
  const [routes, setRoutes] = useState<SafariRoute[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])

  // Selection states
  const [selectedStation, setSelectedStation] = useState<CameraStation | null>(null)
  const [selectedTiger, setSelectedTiger] = useState<TigerLocation | null>(null)
  const [selectedZone, setSelectedZone] = useState<SightseeingZone | null>(null)
  const [focusedLocation, setFocusedLocation] = useState<{ lat: number; lng: number; label?: string } | null>(null)

  // Spot Tiger Modal State
  const [showSpotModal, setShowSpotModal] = useState<boolean>(false)
  const [clickedMapCoords, setClickedMapCoords] = useState<{ lat: number; lng: number; nearestLandmark?: string } | null>(null)

  // Dynamic Alerts Filter & Management
  const [alertSeverityFilter, setAlertSeverityFilter] = useState<string>("ALL")
  const [alertStatusFilter, setAlertStatusFilter] = useState<string>("ALL")
  const [selectedAlertForModal, setSelectedAlertForModal] = useState<Alert | null>(null)
  const [simulatingAlert, setSimulatingAlert] = useState<boolean>(false)
  const [toastNotification, setToastNotification] = useState<string | null>(null)

  const loadDashboardData = async () => {
    try {
      const [dash, stns, tgrs, zns, rts] = await Promise.all([
        api.getDashboard(),
        api.getStations(),
        api.getTigerLocations(),
        api.getSightseeingZones(),
        api.getSafariRoutes()
      ])
      setData(dash)
      setAlerts(dash.alerts || [])
      setStations(stns)
      setTigers(tgrs)
      setZones(zns)
      setRoutes(rts)
      if (stns.length > 0) setSelectedStation(stns[0])
    } catch (err) {
      console.error("Failed to load dashboard telemetry:", err)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  // Handle Sighting Plotted callback
  const handleSightingPlotted = (result: any) => {
    setToastNotification(`Plotted ${result.sighting.tiger_code} (${result.sighting.tiger_name}) at ${result.sighting.location_name}`)
    // Re-fetch or update local tiger array
    api.getTigerLocations().then(setTigers)
    api.getDashboard().then(dash => setAlerts(dash.alerts || []))
    // Focus map on newly spotted tiger location
    setFocusedLocation({
      lat: result.sighting.latitude,
      lng: result.sighting.longitude,
      label: `Just Spotted: ${result.sighting.tiger_code} (${result.sighting.tiger_name})`
    })
    setTimeout(() => setToastNotification(null), 5000)
  }

  // Handle Dynamic Alert Simulation
  const handleSimulateAlert = async () => {
    setSimulatingAlert(true)
    try {
      const newAlert = await api.simulateTelemetryAlert()
      setAlerts(prev => [newAlert, ...prev])
      setToastNotification(`New Alert Generated: ${newAlert.title}`)
      if (newAlert.latitude && newAlert.longitude) {
        setFocusedLocation({
          lat: newAlert.latitude,
          lng: newAlert.longitude,
          label: `${newAlert.tiger_code || "Incident"} - ${newAlert.title}`
        })
      }
      setTimeout(() => setToastNotification(null), 5000)
    } catch (e) {
      console.error(e)
    } finally {
      setSimulatingAlert(false)
    }
  }

  // Handle Alert Status Progression
  const handleUpdateAlertStatus = (alertId: string, newStatus: string) => {
    setAlerts(prev =>
      prev.map(a => (a.id === alertId ? { ...a, status: newStatus } : a))
    )
    const matched = alerts.find(a => a.id === alertId)
    setToastNotification(`Alert status updated to ${newStatus} for "${matched?.title}"`)
    setTimeout(() => setToastNotification(null), 4000)
  }

  // Handle "Locate on Map" action from alert
  const handleLocateAlertOnMap = (alert: Alert) => {
    if (alert.latitude && alert.longitude) {
      setFocusedLocation({
        lat: alert.latitude,
        lng: alert.longitude,
        label: `${alert.tiger_code || "Alert"} • ${alert.title}`
      })
      setToastNotification(`Map centered on incident (${alert.latitude.toFixed(4)}° N, ${alert.longitude.toFixed(4)}° E)`)
      setTimeout(() => setToastNotification(null), 4000)
    }
  }

  // Filtered Alerts
  const filteredAlerts = alerts.filter(a => {
    const matchesSeverity = alertSeverityFilter === "ALL" || a.severity === alertSeverityFilter
    const matchesStatus = alertStatusFilter === "ALL" || a.status === alertStatusFilter
    return matchesSeverity && matchesStatus
  })

  // Alert Metrics Counters
  const activeAlertsCount = alerts.filter(a => a.status === "ACTIVE" || a.status === "INVESTIGATING").length
  const criticalCount = alerts.filter(a => a.severity === "CRITICAL" && a.status !== "RESOLVED").length
  const highCount = alerts.filter(a => a.severity === "HIGH" && a.status !== "RESOLVED").length

  if (!data) return <div className="p-8 text-center text-ink-500 font-mono">Loading telemetry feed...</div>

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Banner Notice & Realtime Toast */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 shadow-sm">
        <div className="flex items-center gap-3">
          <AlertTriangle size={16} className="text-red-500 shrink-0" />
          <span className="font-semibold tracking-wider font-mono">REAL PENCH GIS TELEMETRY:</span>
          <span>Showing real geographical Pench Tiger Reserve coordinates, live tiger sightings, and spatial alerts.</span>
        </div>

        {toastNotification && (
          <div className="bg-white text-ink-900 border border-ink-100 px-3 py-1 rounded-lg font-mono text-xs animate-bounce shadow-card">
            {toastNotification}
          </div>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "Processed Images", val: data.metrics.images_processed.toLocaleString(), icon: Database, color: "text-blue-500" },
          { label: "Quarantined (Blanks)", val: data.metrics.quarantined.toLocaleString(), icon: ShieldAlert, color: "text-red-500" },
          { label: "Storage Saved", val: `${(data.metrics.storage_saved_bytes / 1e12).toFixed(1)} TB`, icon: Compass, color: "text-emerald-500" },
          { label: "Known Individuals", val: `${tigers.length} Resident Tigers`, icon: Eye, color: "text-gold-500" },
        ].map((m, i) => {
          const Icon = m.icon
          return (
            <Card key={i} className="flex items-center justify-between border-l-4 border-l-gold-400 shadow-sm bg-white">
              <div>
                <p className="text-xs text-ink-500 font-mono uppercase tracking-wider">{m.label}</p>
                <h3 className="text-2xl font-black font-serif mt-1 text-ink-900">{m.val}</h3>
              </div>
              <Icon size={28} className={m.color} />
            </Card>
          )
        })}
      </div>

      {/* Real Pench Map Section */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-serif font-black text-xl text-ink-900 flex items-center gap-2">
              <Sparkles size={20} className="text-gold-400" />
              Pench Tiger Reserve Real Geographical Map
            </h2>
            <p className="text-xs font-mono text-ink-500 mt-0.5">
              Click anywhere on the real map to auto-detect coordinates and plot a tiger sighting, or click markers for telemetry details
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              onClick={() => {
                setClickedMapCoords(null)
                setShowSpotModal(true)
              }}
              className="text-xs font-mono uppercase font-bold bg-gold-400 text-white hover:bg-gold-500 flex items-center gap-1.5 shadow-sm"
            >
              <PlusCircle size={14} /> Spot & Plot Tiger
            </Button>

            <Button
              variant="outline"
              onClick={() => navigate("/safari")}
              className="text-xs font-mono text-gold-500 hover:text-gold-600 border-gold-400 hover:border-gold-500 flex items-center gap-1.5 shadow-sm"
            >
              <Compass size={14} /> Safari Route Planner
            </Button>
          </div>
        </div>

        {/* Real Pench GIS Leaflet Map */}
        <RealPenchMap
          tigers={tigers}
          zones={zones}
          stations={stations}
          routes={routes}
          selectedTigerId={selectedTiger?.id}
          selectedStationCode={selectedStation?.code}
          focusedLocation={focusedLocation}
          onSelectTiger={setSelectedTiger}
          onSelectZone={setSelectedZone}
          onSelectStation={setSelectedStation}
          onMapClickToSpot={(coords) => {
            setClickedMapCoords(coords)
            setShowSpotModal(true)
          }}
          onNavigateToSafari={(code) => navigate("/safari")}
        />
      </div>

      {/* Dynamic Alerts Center & Telemetry Stats Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Dynamic Alerts Feed (8 Columns) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="bg-white border border-ink-100 rounded-2xl p-4 shadow-card">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink-100 pb-3 mb-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-red-50 border border-red-200 flex items-center justify-center text-red-500">
                  <Bell size={18} className={criticalCount > 0 ? "animate-pulse" : ""} />
                </div>
                <div>
                  <h3 className="font-serif font-bold text-lg text-ink-900 flex items-center gap-2">
                    Dynamic Telemetry Alerts Center
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-mono font-bold bg-red-100 text-red-700 border border-red-200">
                      {activeAlertsCount} Active
                    </span>
                  </h3>
                  <p className="text-xs text-ink-500 font-mono">
                    Real-time conservation telemetry incidents, buffer movements, and camera anomalies
                  </p>
                </div>
              </div>

              <Button
                variant="primary"
                onClick={handleSimulateAlert}
                disabled={simulatingAlert}
                className="text-xs font-mono uppercase font-bold bg-gold-400 text-white hover:bg-gold-500 shadow-sm flex items-center gap-1.5"
              >
                <Plus size={14} /> {simulatingAlert ? "Generating..." : "Simulate Live Alert"}
              </Button>
            </div>

            {/* Quick Filter Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar text-xs font-mono">
                <span className="text-ink-500 mr-1 flex items-center gap-1"><Filter size={11} /> Severity:</span>
                {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map(sev => (
                  <button
                    key={sev}
                    onClick={() => setAlertSeverityFilter(sev)}
                    className={`px-3 py-1 rounded-full transition-all ${
                      alertSeverityFilter === sev
                        ? "bg-gold-400 text-white font-bold shadow-sm"
                        : "bg-page-50 text-ink-500 hover:text-ink-900 border border-ink-100"
                    }`}
                  >
                    {sev}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-1.5 text-xs font-mono">
                <span className="text-ink-500 mr-1">Status:</span>
                {["ALL", "ACTIVE", "INVESTIGATING", "RESOLVED"].map(st => (
                  <button
                    key={st}
                    onClick={() => setAlertStatusFilter(st)}
                    className={`px-3 py-1 rounded-full transition-all ${
                      alertStatusFilter === st
                        ? "bg-gold-400 text-white font-bold shadow-sm"
                        : "bg-page-50 text-ink-500 hover:text-ink-900 border border-ink-100"
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Alerts List */}
          <div className="space-y-3 max-h-[460px] overflow-y-auto no-scrollbar">
            {filteredAlerts.length === 0 ? (
              <div className="p-12 text-center text-ink-400 font-mono bg-page-50 rounded-2xl border border-ink-100">
                No alerts match the selected filter criteria.
              </div>
            ) : (
              filteredAlerts.map((alert) => {
                const isCritical = alert.severity === "CRITICAL"
                const isHigh = alert.severity === "HIGH"
                const isResolved = alert.status === "RESOLVED"

                return (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-2xl border transition-all duration-300 ${
                      isResolved
                        ? "bg-white border-ink-100 opacity-70"
                        : isCritical
                        ? "bg-red-50 border-red-200 shadow-sm"
                        : isHigh
                        ? "bg-amber-50 border-amber-200 shadow-sm"
                        : "bg-blue-50 border-blue-200"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                          isCritical
                            ? "bg-red-100 text-red-700 border-red-300 animate-pulse"
                            : isHigh
                            ? "bg-amber-100 text-amber-700 border-amber-300"
                            : "bg-blue-100 text-blue-700 border-blue-300"
                        }`}>
                          {alert.severity}
                        </span>

                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                          isResolved
                            ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
                            : alert.status === "INVESTIGATING"
                            ? "bg-yellow-100 text-yellow-700 border border-yellow-300"
                            : "bg-page-100 text-ink-700 border border-ink-200"
                        }`}>
                          {alert.status}
                        </span>

                        {alert.tiger_code && (
                          <span className="font-mono text-xs font-bold text-gold-600 px-2 py-0.5 rounded bg-white border border-ink-100 flex items-center gap-1">
                            <Eye size={12} /> {alert.tiger_code} {alert.tiger_name ? `(${alert.tiger_name})` : ""}
                          </span>
                        )}
                      </div>

                      <span className="text-[11px] font-mono text-ink-400">
                        {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <h4 className="font-serif font-bold text-base text-ink-900 mb-1">{alert.title}</h4>
                    <p className="text-xs text-ink-600 leading-relaxed mb-3">{alert.summary}</p>

                    <div className="border-t border-ink-100 pt-2.5 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                      <div className="flex items-center gap-2">
                        {alert.latitude && alert.longitude && (
                          <button
                            onClick={() => handleLocateAlertOnMap(alert)}
                            className="px-2.5 py-1 rounded-lg bg-white hover:bg-page-50 text-gold-500 flex items-center gap-1.5 transition-colors border border-ink-100"
                          >
                            <MapPin size={13} /> Locate on Map
                          </button>
                        )}

                        <button
                          onClick={() => setSelectedAlertForModal(alert)}
                          className="px-2.5 py-1 rounded-lg bg-page-50 hover:bg-page-100 text-ink-600 flex items-center gap-1 transition-colors border border-ink-100"
                        >
                          <ExternalLink size={12} /> Sensor Evidence
                        </button>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {alert.status !== "RESOLVED" && (
                          <>
                            {alert.status !== "INVESTIGATING" && (
                              <button
                                onClick={() => handleUpdateAlertStatus(alert.id, "INVESTIGATING")}
                                className="px-2.5 py-1 rounded-lg bg-yellow-100 hover:bg-yellow-200 text-yellow-700 border border-yellow-300 transition-colors"
                              >
                                Investigate
                              </button>
                            )}
                            <button
                              onClick={() => handleUpdateAlertStatus(alert.id, "RESOLVED")}
                              className="px-2.5 py-1 rounded-lg bg-emerald-100 hover:bg-emerald-200 text-emerald-700 border border-emerald-300 transition-colors flex items-center gap-1"
                            >
                              <CheckCircle2 size={12} /> Mark Resolved
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Telemetry Stats & Station Status (4 Columns) */}
        <div className="lg:col-span-4 space-y-6 flex flex-col justify-between">
          <Card className="flex-1 flex flex-col justify-between shadow-card bg-white border border-ink-100 p-4 rounded-xl">
            <div>
              <div className="flex items-center justify-between border-b border-ink-100 pb-3 mb-4">
                <h3 className="font-serif font-bold text-lg text-ink-900">Station Telemetry</h3>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                  selectedStation?.status === "ACTIVE" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"
                }`}>
                  {selectedStation?.status || "SELECT STN"}
                </span>
              </div>

              {selectedStation ? (
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-ink-500 font-mono text-xs">Code</span>
                    <span className="font-bold text-ink-900 font-mono">{selectedStation.code}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-500 font-mono text-xs">Name</span>
                    <span className="font-semibold text-ink-700">{selectedStation.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-500 font-mono text-xs">Coordinates</span>
                    <span className="font-mono text-xs text-ink-600">{selectedStation.latitude.toFixed(4)}° N, {selectedStation.longitude.toFixed(4)}° E</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-500 font-mono text-xs">Zone</span>
                    <span className="px-2 py-0.5 bg-page-100 border border-ink-100 rounded text-xs text-ink-700">{selectedStation.zone}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-500 font-mono text-xs">LoRa Telemetry</span>
                    <span className="text-emerald-600 font-mono text-xs font-semibold">Mesh Link Nominal (99.8%)</span>
                  </div>
                </div>
              ) : (
                <p className="text-ink-400 text-center text-sm py-10 font-mono">Select a pin on the map</p>
              )}
            </div>

            <div className="mt-6 border-t border-ink-100 pt-4">
              <h4 className="text-xs font-mono uppercase tracking-wider text-ink-500 mb-2">Weekly Activity Index</h4>
              <div className="h-28 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorImages" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#d4994b" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#d4994b" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="name" stroke="#8a968e" fontSize={9} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #e1e5df", borderRadius: "8px", color: "#1e3529" }} />
                    <Area type="monotone" dataKey="images" stroke="#d4994b" fillOpacity={1} fill="url(#colorImages)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </Card>

          <Card className="bg-white border border-ink-100 p-4 shadow-card">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-serif font-bold text-sm text-ink-900 flex items-center gap-1.5">
                <Compass size={15} className="text-gold-400" /> Best Safari Route Today
              </h4>
              <span className="text-[10px] font-mono text-emerald-600 font-bold">94% Visibility</span>
            </div>
            <p className="text-xs text-ink-600 mb-3">
              Touria Prime Core Circuit has active tiger sightings for Baghira & Tara around Alikatta Meadow.
            </p>
            <Button
              variant="outline"
              onClick={() => navigate("/safari")}
              className="w-full text-xs font-mono uppercase font-bold py-2 border-ink-200 text-gold-500 hover:bg-page-50"
            >
              View Full Route Blueprint →
            </Button>
          </Card>
        </div>
      </div>

      {/* Spot Tiger Modal */}
      <SpotTigerModal
        isOpen={showSpotModal}
        onClose={() => setShowSpotModal(false)}
        initialCoords={clickedMapCoords}
        tigers={tigers}
        onSightingPlotted={handleSightingPlotted}
      />

      {/* Sensor Evidence Modal */}
      <Dialog
        isOpen={!!selectedAlertForModal}
        onClose={() => setSelectedAlertForModal(null)}
        title={`Incident Sensor Telemetry: ${selectedAlertForModal?.title || ""}`}
      >
        {selectedAlertForModal && (
          <div className="space-y-4 text-ink-900">
            <div className="p-3 bg-surface-inset border border-ink-100 rounded-xl space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-mono text-ink-500">Incident Severity:</span>
                <span className="font-mono font-bold text-red-600">{selectedAlertForModal.severity}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-mono text-ink-500">Current Status:</span>
                <span className="font-mono font-bold text-emerald-600">{selectedAlertForModal.status}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-mono text-ink-500">Detection Station:</span>
                <span className="font-mono font-bold text-gold-500">{selectedAlertForModal.station_code || "CT-07"}</span>
              </div>
            </div>

            <div className="bg-page-50 p-3 rounded-xl border border-ink-100 text-xs space-y-1">
              <h4 className="font-bold text-ink-700 uppercase font-mono">Recommended Ranger Action</h4>
              <p className="text-ink-600 leading-relaxed">
                {selectedAlertForModal.action_recommendation || "Dispatch patrol team to verify perimeter sensor triggers."}
              </p>
            </div>

            <div className="flex gap-2 pt-2">
              {selectedAlertForModal.latitude && selectedAlertForModal.longitude && (
                <Button
                  variant="outline"
                  className="flex-1 text-xs uppercase"
                  onClick={() => {
                    handleLocateAlertOnMap(selectedAlertForModal)
                    setSelectedAlertForModal(null)
                  }}
                >
                  Locate on Map
                </Button>
              )}
              <Button
                variant="primary"
                className="flex-1 text-xs uppercase font-bold bg-gold-400 text-white hover:bg-gold-500"
                onClick={() => setSelectedAlertForModal(null)}
              >
                Close Evidence Card
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  )
}

export default DashboardPage
