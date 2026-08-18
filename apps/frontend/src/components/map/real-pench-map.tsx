import React, { useEffect, useRef, useState } from "react"
import L from "leaflet"
import {
  TigerLocation,
  SightseeingZone,
  CameraStation,
  SafariRoute
} from "../../lib/types"
import {
  Compass,
  MapPin,
  Layers,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sunrise,
  Sun,
  Moon,
  Crosshair,
  Sparkles,
  X,
  Navigation,
  Globe,
  Radio,
  Eye,
  PlusCircle
} from "lucide-react"

// Real Pench Geographical GeoJSON Features
const PENCH_CORE_BOUNDS: [number, number][] = [
  [21.7850, 79.2850],
  [21.7920, 79.3250],
  [21.7750, 79.3650],
  [21.7450, 79.3800],
  [21.7100, 79.3650],
  [21.6850, 79.3350],
  [21.6800, 79.2850],
  [21.7050, 79.2450],
  [21.7450, 79.2550],
  [21.7850, 79.2850]
]

const TOTLADOH_RESERVOIR_BOUNDS: [number, number][] = [
  [21.7800, 79.2800],
  [21.7950, 79.3050],
  [21.7700, 79.3200],
  [21.7550, 79.3000],
  [21.7650, 79.2750],
  [21.7800, 79.2800]
]

const PENCH_RIVER_LINE: [number, number][] = [
  [21.8000, 79.2900],
  [21.7700, 79.3000],
  [21.7450, 79.3150],
  [21.7250, 79.3300],
  [21.7000, 79.3450],
  [21.6750, 79.3600]
]

interface RealPenchMapProps {
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
  onMapClickToSpot?: (coords: { lat: number; lng: number; nearestLandmark: string }) => void
  onNavigateToSafari?: (routeCode?: string) => void
}

export const RealPenchMap: React.FC<RealPenchMapProps> = ({
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
  onMapClickToSpot,
  onNavigateToSafari
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const layerGroupsRef = useRef<{ [key: string]: L.LayerGroup }>({})
  const tileLayerRef = useRef<L.TileLayer | null>(null)
  const focusMarkerRef = useRef<L.Marker | null>(null)

  // Map Tile Style: Light (CartoDB Positron), Satellite (Esri), Topo (OpenTopo)
  const [mapStyle, setMapStyle] = useState<"DARK" | "SATELLITE" | "TOPO">("DARK")

  // Layer Toggles
  const [showTigers, setShowTigers] = useState<boolean>(true)
  const [showZones, setShowZones] = useState<boolean>(true)
  const [showStations, setShowStations] = useState<boolean>(true)
  const [showRoutes, setShowRoutes] = useState<boolean>(true)
  const [showBoundaries, setShowBoundaries] = useState<boolean>(true)

  // Spot Tiger on Map Mode
  const [spottingModeActive, setSpottingModeActive] = useState<boolean>(false)

  // Time-of-day filter
  const [timeSlot, setTimeSlot] = useState<"MORNING" | "AFTERNOON" | "NIGHT">("MORNING")

  // Active Inspection Entities
  const [activeTiger, setActiveTiger] = useState<TigerLocation | null>(null)
  const [activeZone, setActiveZone] = useState<SightseeingZone | null>(null)
  const [activeStation, setActiveStation] = useState<CameraStation | null>(null)
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lng: number }>({ lat: 21.7350, lng: 79.3100 })

  // Find nearest landmark to coordinates
  const getNearestLandmark = (lat: number, lng: number): string => {
    let nearest = "Alikatta Meadow Core"
    let minDist = 999
    zones.forEach(z => {
      const d = Math.hypot(z.latitude - lat, z.longitude - lng)
      if (d < minDist) {
        minDist = d
        nearest = z.name
      }
    })
    return nearest
  }

  // 1. Initialize Leaflet Map Instance
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return

    // Center on real Pench Tiger Reserve coordinates
    const map = L.map(mapContainerRef.current, {
      center: [21.7350, 79.3100],
      zoom: 12,
      minZoom: 10,
      maxZoom: 18,
      zoomControl: false,
      attributionControl: false
    })

    // Add Tile Layer
    const tileUrl =
      mapStyle === "SATELLITE"
        ? "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        : mapStyle === "TOPO"
        ? "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
        : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"

    tileLayerRef.current = L.tileLayer(tileUrl, { maxZoom: 19 }).addTo(map)

    // Layer Groups
    layerGroupsRef.current = {
      boundaries: L.layerGroup().addTo(map),
      water: L.layerGroup().addTo(map),
      routes: L.layerGroup().addTo(map),
      zones: L.layerGroup().addTo(map),
      stations: L.layerGroup().addTo(map),
      tigers: L.layerGroup().addTo(map)
    }

    // Mousemove for HUD coordinates
    map.on("mousemove", (e: L.LeafletMouseEvent) => {
      setCursorCoords({ lat: e.latlng.lat, lng: e.latlng.lng })
    })

    // Click handler for "Spot Tiger" on map
    map.on("click", (e: L.LeafletMouseEvent) => {
      const nearest = getNearestLandmark(e.latlng.lat, e.latlng.lng)
      if (onMapClickToSpot) {
        onMapClickToSpot({
          lat: Number(e.latlng.lat.toFixed(5)),
          lng: Number(e.latlng.lng.toFixed(5)),
          nearestLandmark: nearest
        })
      }
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // 2. Handle Tile Style Switching
  useEffect(() => {
    if (!mapRef.current || !tileLayerRef.current) return
    const tileUrl =
      mapStyle === "SATELLITE"
        ? "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        : mapStyle === "TOPO"
        ? "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
        : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"

    tileLayerRef.current.setUrl(tileUrl)
  }, [mapStyle])

  // 3. Render Real GIS Boundaries & Waterbody
  useEffect(() => {
    if (!mapRef.current) return
    const boundaryGroup = layerGroupsRef.current.boundaries
    const waterGroup = layerGroupsRef.current.water
    boundaryGroup.clearLayers()
    waterGroup.clearLayers()

    if (showBoundaries) {
      // Pench Core Zone Polygon
      L.polygon(PENCH_CORE_BOUNDS, {
        color: "#e5a44d",
        weight: 2,
        dashArray: "6, 4",
        fillColor: "#1b4332",
        fillOpacity: 0.12
      }).bindTooltip("PENCH NATIONAL PARK · CORE SECTOR", { permanent: false, className: "font-mono text-xs" }).addTo(boundaryGroup)

      // Totladoh Reservoir Lake
      L.polygon(TOTLADOH_RESERVOIR_BOUNDS, {
        color: "#38bdf8",
        weight: 1.5,
        fillColor: "#0284c7",
        fillOpacity: 0.35
      }).bindTooltip("TOTLADOH RESERVOIR DAM BASIN", { permanent: false, className: "font-mono text-xs" }).addTo(waterGroup)

      // Pench River Line
      L.polyline(PENCH_RIVER_LINE, {
        color: "#38bdf8",
        weight: 4,
        opacity: 0.65
      }).bindTooltip("PENCH PERENNIAL RIVER", { permanent: false, className: "font-mono text-xs" }).addTo(waterGroup)
    }
  }, [showBoundaries])

  // 4. Render Sightseeing Zones
  useEffect(() => {
    if (!mapRef.current) return
    const group = layerGroupsRef.current.zones
    group.clearLayers()

    if (!showZones) return

    zones.forEach(zone => {
      const score =
        timeSlot === "MORNING"
          ? zone.visibility_score_morning
          : timeSlot === "AFTERNOON"
          ? zone.visibility_score_afternoon
          : zone.visibility_score_night

      const isUltra = score >= 90
      const color = isUltra ? "#10b981" : "#e5a44d"

      const circle = L.circle([zone.latitude, zone.longitude], {
        radius: zone.radius_meters,
        color: color,
        weight: 2,
        dashArray: "4, 4",
        fillColor: color,
        fillOpacity: isUltra ? 0.22 : 0.16
      })

      // Marker Pill in Center
      const icon = L.divIcon({
        className: "custom-zone-marker",
        html: `
          <div style="transform: translate(-50%, -50%);" class="px-2 py-0.5 rounded-lg bg-white/95 border border-${isUltra ? 'emerald' : 'amber'}-400 text-[10px] font-mono font-bold text-ink-900 shadow-md flex items-center gap-1 cursor-pointer whitespace-nowrap">
            <span class="w-1.5 h-1.5 rounded-full ${isUltra ? 'bg-emerald-500' : 'bg-amber-500'} animate-pulse"></span>
            ${score}% · ${zone.name.split(" ")[0]}
          </div>
        `,
        iconSize: [0, 0]
      })

      const centerMarker = L.marker([zone.latitude, zone.longitude], { icon })

      const handleZoneClick = () => {
        setActiveZone(zone)
        setActiveTiger(null)
        setActiveStation(null)
        if (onSelectZone) onSelectZone(zone)
      }

      circle.on("click", handleZoneClick)
      centerMarker.on("click", handleZoneClick)

      circle.addTo(group)
      centerMarker.addTo(group)
    })
  }, [zones, showZones, timeSlot])

  // 5. Render Safari Tracks
  useEffect(() => {
    if (!mapRef.current) return
    const group = layerGroupsRef.current.routes
    group.clearLayers()

    if (!showRoutes) return

    routes.forEach(route => {
      if (route.waypoints && route.waypoints.length > 1) {
        const latlngs: [number, number][] = route.waypoints.map(w => [w.latitude, w.longitude])
        const polyline = L.polyline(latlngs, {
          color: route.code === "PTR-SR-01" ? "#fbbf24" : route.code === "PTR-SR-02" ? "#34d399" : "#a78bfa",
          weight: 3,
          dashArray: "6, 4",
          opacity: 0.85
        })

        polyline.bindTooltip(`${route.code} - ${route.name} (${route.visibility_rating}% Tiger Rate)`, {
          className: "font-mono text-xs"
        })

        polyline.addTo(group)
      }
    })
  }, [routes, showRoutes])

  // 6. Render Camera Stations
  useEffect(() => {
    if (!mapRef.current) return
    const group = layerGroupsRef.current.stations
    group.clearLayers()

    if (!showStations) return

    stations.forEach(stn => {
      const isSelected = selectedStationCode === stn.code || activeStation?.code === stn.code
      const icon = L.divIcon({
        className: "station-pin",
        html: `
          <div style="transform: translate(-50%, -50%);" class="flex items-center gap-1 cursor-pointer">
            <div class="w-3.5 h-3.5 rounded-full ${stn.status === 'ACTIVE' ? 'bg-emerald-500' : 'bg-red-400'} border-2 border-white shadow-sm flex items-center justify-center"></div>
            <span class="px-1.5 py-0.5 rounded bg-white/95 border border-ink-200 text-[9px] font-mono font-bold text-ink-900 shadow-sm">${stn.code}</span>
          </div>
        `,
        iconSize: [0, 0]
      })

      const marker = L.marker([stn.latitude, stn.longitude], { icon })
      marker.on("click", () => {
        setActiveStation(stn)
        setActiveTiger(null)
        setActiveZone(null)
        if (onSelectStation) onSelectStation(stn)
      })
      marker.addTo(group)
    })
  }, [stations, showStations, selectedStationCode, activeStation])

  // 7. Render Plotted Tigers with Real Pulse Markers & Movement Trails
  useEffect(() => {
    if (!mapRef.current) return
    const group = layerGroupsRef.current.tigers
    group.clearLayers()

    if (!showTigers) return

    tigers.forEach(tiger => {
      const isSelected = selectedTigerId === tiger.id || activeTiger?.id === tiger.id

      // Movement trail line if available
      if (tiger.recent_coordinates && tiger.recent_coordinates.length > 1) {
        const lineCoords: [number, number][] = tiger.recent_coordinates.map(c => [c.lat, c.lng])
        L.polyline(lineCoords, {
          color: "#e5a44d",
          weight: 2,
          dashArray: "4, 3",
          opacity: 0.75
        }).addTo(group)
      }

      // Custom animated tiger pin
      const icon = L.divIcon({
        className: "tiger-pulse-marker",
        html: `
          <div style="transform: translate(-50%, -50%);" class="relative flex items-center justify-center cursor-pointer group">
            <div class="tiger-pulse-halo"></div>
            <div class="w-6 h-6 rounded-lg bg-gold-400 border-2 border-white rotate-45 flex items-center justify-center shadow-md z-10 transition-transform group-hover:scale-125">
              <span class="-rotate-45 text-[9px] font-bold text-white">T</span>
            </div>
            <div class="absolute top-7 px-2 py-0.5 rounded-full bg-white border border-gold-400 text-[9px] font-mono font-bold text-ink-900 shadow-md whitespace-nowrap z-20">
              ${tiger.code} - ${tiger.name}
            </div>
          </div>
        `,
        iconSize: [0, 0]
      })

      const marker = L.marker([tiger.latitude, tiger.longitude], { icon })
      marker.on("click", () => {
        setActiveTiger(tiger)
        setActiveZone(null)
        setActiveStation(null)
        if (onSelectTiger) onSelectTiger(tiger)
      })
      marker.addTo(group)
    })
  }, [tigers, showTigers, selectedTigerId, activeTiger])

  // 8. Handle External Focus / FlyTo (from Alerts or Sighting Click)
  useEffect(() => {
    if (!mapRef.current || !focusedLocation) return

    mapRef.current.flyTo([focusedLocation.lat, focusedLocation.lng], 14, { duration: 1.2 })

    if (focusMarkerRef.current) {
      focusMarkerRef.current.remove()
    }

    const focusIcon = L.divIcon({
      className: "focus-crosshair",
      html: `
        <div style="transform: translate(-50%, -50%);" class="relative flex items-center justify-center">
          <div class="w-12 h-12 rounded-full border-2 border-red-500 animate-ping absolute"></div>
          <div class="w-6 h-6 rounded-full bg-red-500 border-2 border-white flex items-center justify-center text-white text-[10px] font-bold">!</div>
          <div class="absolute top-8 px-2 py-0.5 rounded bg-white border border-red-400 text-[9px] font-mono text-red-700 font-bold whitespace-nowrap shadow-md">
            ${focusedLocation.label || "TARGET INCIDENT"}
          </div>
        </div>
      `,
      iconSize: [0, 0]
    })

    const marker = L.marker([focusedLocation.lat, focusedLocation.lng], { icon: focusIcon }).addTo(mapRef.current)
    focusMarkerRef.current = marker
  }, [focusedLocation])

  const handleZoomIn = () => mapRef.current?.zoomIn()
  const handleZoomOut = () => mapRef.current?.zoomOut()
  const handleReset = () => {
    mapRef.current?.flyTo([21.7350, 79.3100], 12, { duration: 1.0 })
    setActiveTiger(null)
    setActiveZone(null)
    setActiveStation(null)
  }

  return (
    <div className="relative w-full h-[580px] rounded-2xl overflow-hidden border border-ink-100 bg-page-100 shadow-card-lg flex flex-col select-none">
      {/* Top Floating Controls Bar */}
      <div className="absolute top-4 left-4 right-4 z-[1000] flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Left: Pench Real Map Indicator & Satellite Switcher */}
        <div className="flex items-center gap-2 pointer-events-auto">
          <div className="bg-white/95 backdrop-blur-sm px-3.5 py-2 rounded-xl border border-ink-100 flex items-center gap-2.5 shadow-card">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <div>
              <h3 className="font-serif font-bold text-xs text-ink-900 leading-none">REAL PENCH GIS TELEMETRY</h3>
              <p className="text-[9px] font-mono text-ink-400 leading-tight mt-0.5">
                {tigers.length} Tigers Plotted &middot; {zones.length} Hotspots Active
              </p>
            </div>
          </div>

          {/* Map Tile Layer Selector */}
          <div className="bg-white/95 backdrop-blur-sm p-1 rounded-xl border border-ink-100 flex items-center gap-1 shadow-card">
            <button
              onClick={() => setMapStyle("DARK")}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                mapStyle === "DARK" ? "bg-gold-400 text-white shadow-sm" : "text-ink-500 hover:text-ink-900"
              }`}
            >
              Light Topo
            </button>
            <button
              onClick={() => setMapStyle("SATELLITE")}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                mapStyle === "SATELLITE" ? "bg-gold-400 text-white shadow-sm" : "text-ink-500 hover:text-ink-900"
              }`}
            >
              Satellite
            </button>
            <button
              onClick={() => setMapStyle("TOPO")}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                mapStyle === "TOPO" ? "bg-gold-400 text-white shadow-sm" : "text-ink-500 hover:text-ink-900"
              }`}
            >
              Terrain
            </button>
          </div>
        </div>

        {/* Center: Time-of-Day Sighting Filter */}
        <div className="bg-white/95 backdrop-blur-sm p-1 rounded-xl border border-ink-100 flex items-center gap-1 shadow-card pointer-events-auto">
          <button
            onClick={() => setTimeSlot("MORNING")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              timeSlot === "MORNING"
                ? "bg-amber-50 text-amber-700 border border-amber-300 font-bold"
                : "text-ink-500 hover:text-ink-900"
            }`}
          >
            <Sunrise size={13} className="text-amber-500" />
            <span>Dawn (06:00-09:30)</span>
          </button>

          <button
            onClick={() => setTimeSlot("AFTERNOON")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              timeSlot === "AFTERNOON"
                ? "bg-orange-50 text-orange-700 border border-orange-300 font-bold"
                : "text-ink-500 hover:text-ink-900"
            }`}
          >
            <Sun size={13} className="text-orange-500" />
            <span>Dusk (15:30-18:30)</span>
          </button>

          <button
            onClick={() => setTimeSlot("NIGHT")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              timeSlot === "NIGHT"
                ? "bg-indigo-50 text-indigo-700 border border-indigo-300 font-bold"
                : "text-ink-500 hover:text-ink-900"
            }`}
          >
            <Moon size={13} className="text-indigo-500" />
            <span>Night Buffer</span>
          </button>
        </div>

        {/* Right: "Spot Tiger on Map" Quick Pin Action & Zoom */}
        <div className="flex items-center gap-2 pointer-events-auto">
          <button
            onClick={() => {
              if (onMapClickToSpot) {
                onMapClickToSpot({
                  lat: 21.7432,
                  lng: 79.3215,
                  nearestLandmark: "Alikatta Meadow Hotspot"
                })
              }
            }}
            className="bg-gold-400 hover:bg-gold-500 px-3 py-2 rounded-xl text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all"
          >
            <PlusCircle size={14} />
            <span>Spot & Plot Tiger</span>
          </button>

          {/* Zoom Buttons */}
          <div className="bg-white/95 backdrop-blur-sm p-1 rounded-xl border border-ink-100 flex items-center gap-1 shadow-card">
            <button onClick={handleZoomIn} className="p-1.5 rounded-lg text-ink-500 hover:text-ink-900 hover:bg-page-200" title="Zoom In">
              <ZoomIn size={15} />
            </button>
            <button onClick={handleZoomOut} className="p-1.5 rounded-lg text-ink-500 hover:text-ink-900 hover:bg-page-200" title="Zoom Out">
              <ZoomOut size={15} />
            </button>
            <button onClick={handleReset} className="p-1.5 rounded-lg text-ink-500 hover:text-ink-900 hover:bg-page-200" title="Reset View">
              <RotateCcw size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Leaflet Map Canvas */}
      <div ref={mapContainerRef} className="w-full h-full z-0 cursor-crosshair" />

      {/* Bottom Left HUD: Coordinates & Scale */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-white/95 backdrop-blur-sm px-3 py-2 rounded-xl border border-ink-100 flex items-center gap-3 text-[10px] font-mono text-ink-600 pointer-events-none shadow-card">
        <div className="flex items-center gap-1.5">
          <Navigation size={12} className="text-gold-400 rotate-45" />
          <span>{cursorCoords.lat.toFixed(4)}° N, {cursorCoords.lng.toFixed(4)}° E</span>
        </div>
        <div className="w-px h-3 bg-ink-100" />
        <span className="text-forest-500 font-semibold">PENCH CORE RESERVE</span>
        <div className="w-px h-3 bg-ink-100" />
        <span className="text-gold-500 font-bold">CLICK TO SPOT</span>
      </div>

      {/* Bottom Right Layer Legend */}
      <div className="absolute bottom-4 right-4 z-[1000] bg-white/95 backdrop-blur-sm p-2.5 rounded-xl border border-ink-100 flex items-center gap-3 text-xs font-mono text-ink-600 shadow-card">
        <button
          onClick={() => setShowTigers(!showTigers)}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
            showTigers ? "bg-amber-50 text-amber-700" : "text-ink-300 line-through"
          }`}
        >
          <span className="w-2.5 h-2.5 rounded-sm bg-gold-400" />
          <span>Tigers ({tigers.length})</span>
        </button>

        <button
          onClick={() => setShowZones(!showZones)}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
            showZones ? "bg-emerald-50 text-emerald-700" : "text-ink-300 line-through"
          }`}
        >
          <span className="w-2.5 h-2.5 rounded-full border border-emerald-500" />
          <span>Sightseeing ({zones.length})</span>
        </button>

        <button
          onClick={() => setShowStations(!showStations)}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
            showStations ? "bg-blue-50 text-blue-700" : "text-ink-300 line-through"
          }`}
        >
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span>Stations ({stations.length})</span>
        </button>

        <button
          onClick={() => setShowRoutes(!showRoutes)}
          className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
            showRoutes ? "bg-yellow-50 text-yellow-700" : "text-ink-300 line-through"
          }`}
        >
          <span className="w-3 border-t-2 border-dashed border-yellow-500" />
          <span>Safari Tracks</span>
        </button>
      </div>

      {/* Slide-in Telemetry Inspection Drawer (Tiger / Zone / Station) */}
      {(activeTiger || activeZone || activeStation) && (
        <div className="absolute top-16 right-4 z-[1001] w-80 bg-white rounded-2xl border border-ink-100 p-4 shadow-card-lg animate-fade-in max-h-[460px] overflow-y-auto no-scrollbar">
          <div className="flex items-center justify-between border-b border-ink-100 pb-2.5 mb-3">
            <span className="text-[10px] font-mono text-gold-500 tracking-wider uppercase font-bold flex items-center gap-1.5">
              <Sparkles size={12} />
              {activeTiger ? "Tiger Telemetry Profile" : activeZone ? "Sightseeing Hotspot" : "Camera Station"}
            </span>
            <button
              onClick={() => {
                setActiveTiger(null)
                setActiveZone(null)
                setActiveStation(null)
              }}
              className="text-ink-400 hover:text-ink-900 transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          {/* Tiger Selected State */}
          {activeTiger && (
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gold-50 border border-gold-200 flex items-center justify-center shadow-sm">
                  <Eye size={22} className="text-gold-500" />
                </div>
                <div>
                  <h4 className="font-serif font-bold text-lg text-ink-900 leading-tight">
                    {activeTiger.name} ({activeTiger.code})
                  </h4>
                  <p className="text-[11px] font-mono text-ink-400">
                    {activeTiger.sex} • {activeTiger.approx_zone}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs bg-page-50 p-2.5 rounded-xl border border-ink-100">
                <div>
                  <span className="text-[10px] font-mono text-ink-400 uppercase block">Current Activity</span>
                  <span className="font-bold text-forest-500">{activeTiger.current_activity.replace("_", " ")}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-ink-400 uppercase block">Last Verified</span>
                  <span className="font-bold text-gold-500">{activeTiger.last_seen_relative}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-ink-400 uppercase block">GPS Coordinates</span>
                  <span className="font-mono text-ink-900 text-[11px] font-semibold">{activeTiger.latitude.toFixed(4)}° N, {activeTiger.longitude.toFixed(4)}° E</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-ink-400 uppercase block">Confidence Match</span>
                  <span className="font-mono text-forest-500 font-semibold">{(activeTiger.sighting_confidence * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div className="text-xs text-ink-600 bg-page-50 p-2.5 rounded-xl border border-ink-100">
                <span className="text-[10px] font-mono text-ink-400 uppercase block mb-1">Dominant Waterhole & Habitat</span>
                <p className="font-semibold text-gold-500">{activeTiger.dominant_waterhole}</p>
                <p className="text-[11px] text-ink-400 mt-1">{activeTiger.notes}</p>
              </div>

              {onNavigateToSafari && (
                <button
                  onClick={() => onNavigateToSafari("PTR-SR-01")}
                  className="w-full py-2 bg-gold-400 hover:bg-gold-500 text-white text-xs font-mono font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-sm transition-all"
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
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {activeZone.zone_type} ZONE
                  </span>
                  <span className="font-mono font-bold text-sm text-gold-500">
                    {timeSlot === "MORNING" ? activeZone.visibility_score_morning : timeSlot === "AFTERNOON" ? activeZone.visibility_score_afternoon : activeZone.visibility_score_night}% Visibility
                  </span>
                </div>
                <h4 className="font-serif font-bold text-lg text-ink-900 mt-1">{activeZone.name}</h4>
                <p className="text-xs text-ink-600 mt-1 leading-relaxed">{activeZone.description}</p>
              </div>

              <div className="bg-page-50 p-3 rounded-xl border border-ink-100 space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-ink-600 flex items-center gap-1"><Sunrise size={11} className="text-amber-500" /> Morning Safari:</span>
                  <span className="font-mono font-bold text-amber-600">{activeZone.visibility_score_morning}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-ink-600 flex items-center gap-1"><Sun size={11} className="text-orange-500" /> Afternoon Safari:</span>
                  <span className="font-mono font-bold text-orange-600">{activeZone.visibility_score_afternoon}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-ink-600 flex items-center gap-1"><Moon size={11} className="text-indigo-500" /> Night Buffer:</span>
                  <span className="font-mono font-bold text-indigo-600">{activeZone.visibility_score_night}%</span>
                </div>
              </div>

              <div className="text-[11px] text-ink-500 font-mono">
                <p><strong className="text-ink-700">Recommended Gate:</strong> {activeZone.recommended_gate}</p>
                <p className="mt-0.5"><strong className="text-ink-700">Best Timing:</strong> {activeZone.best_safari_timing}</p>
              </div>
            </div>
          )}

          {/* Camera Station Selected State */}
          {activeStation && (
            <div className="space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-serif font-bold text-lg text-ink-900">{activeStation.name}</h4>
                  <p className="text-xs font-mono text-forest-500 font-semibold">{activeStation.code} &middot; {activeStation.zone} ZONE</p>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {activeStation.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs bg-page-50 p-2.5 rounded-xl border border-ink-100">
                <div>
                  <span className="text-[10px] font-mono text-ink-400 uppercase block">Coordinates</span>
                  <span className="font-mono text-ink-900 text-[11px]">{activeStation.latitude.toFixed(4)}° N, {activeStation.longitude.toFixed(4)}° E</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-ink-400 uppercase block">Telemetry Check</span>
                  <span className="font-mono text-ink-700 text-[11px]">{activeStation.last_check || "Active Online"}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default RealPenchMap
