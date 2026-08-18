import React, { useState, useEffect } from "react"
import { Dialog } from "../ui/dialog"
import { Button } from "../ui/button"
import {
  Sparkles,
  MapPin,
  Compass,
  Radio,
  Eye,
  Crosshair,
  CheckCircle2,
  AlertTriangle,
  Send,
  Navigation
} from "lucide-react"
import { Tiger, TigerLocation } from "../../lib/types"
import { api } from "../../lib/api"

interface SpotTigerModalProps {
  isOpen: boolean
  onClose: () => void
  initialCoords?: { lat: number; lng: number; nearestLandmark?: string } | null
  tigers?: (Tiger | TigerLocation)[]
  onSightingPlotted?: (result: any) => void
}

const PENCH_PRESETS = [
  { name: "Alikatta Central Meadow", lat: 21.7432, lng: 79.3215, zone: "CORE" },
  { name: "Bodhanala Reservoir Shore", lat: 21.7318, lng: 79.3042, zone: "CORE" },
  { name: "Pyorthadi Ghost Tree Basin", lat: 21.7240, lng: 79.3360, zone: "CORE" },
  { name: "Gumtara Bamboo Nullah", lat: 21.7125, lng: 79.2654, zone: "CORE" },
  { name: "Chindimatta High Ridge & Plateau", lat: 21.7556, lng: 79.2876, zone: "CORE" },
  { name: "Totladoh Reservoir Lake", lat: 21.7680, lng: 79.2950, zone: "CORE" },
  { name: "Touria Core Gate Checkpost", lat: 21.7000, lng: 79.3100, zone: "CORE" },
  { name: "Karmajhiri Buffer Gate & Corridor", lat: 21.6901, lng: 79.2888, zone: "BUFFER" },
  { name: "Baghin Nala Culvert", lat: 21.7200, lng: 79.3150, zone: "CORE" },
  { name: "Khursapar Maharashtra Gate", lat: 21.6700, lng: 79.3400, zone: "CORE" },
  { name: "Rukhad Bison Corridor", lat: 21.6500, lng: 79.3100, zone: "BUFFER" },
  { name: "Jamtara Riverbed Wilderness", lat: 21.7681, lng: 79.3398, zone: "CORE" }
]

export const SpotTigerModal: React.FC<SpotTigerModalProps> = ({
  isOpen,
  onClose,
  initialCoords,
  tigers = [],
  onSightingPlotted
}) => {
  const [availableTigers, setAvailableTigers] = useState<(Tiger | TigerLocation)[]>(tigers)
  const [isNewTiger, setIsNewTiger] = useState<boolean>(false)
  const [tigerCode, setTigerCode] = useState<string>("T017")
  const [tigerName, setTigerName] = useState<string>("Baghira")
  const [tigerSex, setTigerSex] = useState<string>("MALE")
  const [locationName, setLocationName] = useState<string>("Alikatta Central Meadow")
  const [latitude, setLatitude] = useState<number>(21.7432)
  const [longitude, setLongitude] = useState<number>(79.3215)
  const [behavior, setBehavior] = useState<string>("Patrolling main dirt road toward Bodhanala; calm demeanor.")
  const [confidence, setConfidence] = useState<number>(95)
  const [observer, setObserver] = useState<string>("GYPSY_NATURALIST")
  const [notes, setNotes] = useState<string>("")
  const [submitting, setSubmitting] = useState<boolean>(false)
  const [autoDetectedBadge, setAutoDetectedBadge] = useState<string | null>(null)

  // Fetch live tigers from DB whenever modal opens
  useEffect(() => {
    if (isOpen) {
      api.getTigers().then(dbTigers => {
        if (dbTigers && dbTigers.length > 0) {
          setAvailableTigers(dbTigers)
          if (!isNewTiger && (!tigerCode || !dbTigers.some(t => t.code === tigerCode))) {
            setTigerCode(dbTigers[0].code)
            setTigerName(dbTigers[0].name || `Tiger ${dbTigers[0].code}`)
            if ((dbTigers[0] as any).sex) setTigerSex((dbTigers[0] as any).sex)
          }
        }
      }).catch(err => {
        console.warn("Could not fetch tigers for modal dropdown:", err)
      })
    }
  }, [isOpen])

  // Sync if tigers prop changes
  useEffect(() => {
    if (tigers && tigers.length > 0) {
      setAvailableTigers(tigers)
    }
  }, [tigers])

  // Update when initialCoords passed from map click
  useEffect(() => {
    if (initialCoords) {
      setLatitude(initialCoords.lat)
      setLongitude(initialCoords.lng)
      if (initialCoords.nearestLandmark) {
        setLocationName(initialCoords.nearestLandmark)
        setAutoDetectedBadge(`Auto-detected near ${initialCoords.nearestLandmark}`)
      } else {
        setAutoDetectedBadge(`Real GPS: ${initialCoords.lat.toFixed(4)}° N, ${initialCoords.lng.toFixed(4)}° E`)
      }
    }
  }, [initialCoords])

  // Handle Location Name change & Auto-Geocoding
  const handleLocationChange = async (name: string) => {
    setLocationName(name)
    const match = PENCH_PRESETS.find(p => p.name.toLowerCase() === name.toLowerCase())
    if (match) {
      setLatitude(match.lat)
      setLongitude(match.lng)
      setAutoDetectedBadge(`Auto-resolved GPS: ${match.lat}° N, ${match.lng}° E (${match.zone} Zone)`)
      return
    }

    if (name.trim().length >= 3) {
      try {
        const geo = await api.geocodeLandmark(name)
        if (geo && geo.latitude && geo.longitude) {
          setLatitude(geo.latitude)
          setLongitude(geo.longitude)
          setAutoDetectedBadge(`Resolved: ${geo.matched_landmark} (${geo.latitude}° N, ${geo.longitude}° E)`)
        }
      } catch (e) {
        // Silent fallback
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!tigerCode.trim() || !locationName.trim() || !behavior.trim()) return

    setSubmitting(true)
    try {
      const payload = {
        tiger_code: tigerCode.trim().toUpperCase(),
        tiger_name: tigerName.trim() || `Tiger ${tigerCode}`,
        tiger_sex: tigerSex,
        location_name: locationName.trim(),
        latitude: Number(latitude),
        longitude: Number(longitude),
        behavior: behavior.trim(),
        confidence_score: confidence / 100,
        observed_by: observer,
        notes: notes.trim() || undefined
      }

      const result = await api.spotAndPlotTiger(payload)

      if (onSightingPlotted) {
        onSightingPlotted(result)
      }

      onClose()
    } catch (err: any) {
      console.error("Failed to spot tiger:", err)
      alert(`Error spotting tiger: ${err.message || "Unknown error"}`)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog isOpen={isOpen} onClose={onClose} title="Spot & Plot Tiger on Real Map">
      <form onSubmit={handleSubmit} className="space-y-4 text-ink-900">
        {/* Banner Notice */}
        <div className="p-3 bg-page-50 border border-ink-100 rounded-xl text-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-bold text-ink-900 flex items-center gap-1.5 font-mono uppercase tracking-wider">
              <Crosshair size={14} className="text-gold-500" /> Real-time Tiger Telemetry Plotter
            </span>
            <span className="text-[10px] font-mono bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded border border-emerald-200 font-bold">
              PostgreSQL Connected
            </span>
          </div>
          <p className="text-ink-600 text-[11px] leading-relaxed">
            Saves to database, updates tiger telemetry history, and plots the marker directly onto the interactive map.
          </p>
        </div>

        {/* Mode Selector: Existing Tiger vs New Individual */}
        <div className="flex items-center gap-2 p-1.5 rounded-xl bg-page-50 border border-ink-100">
          <button
            type="button"
            onClick={() => {
              setIsNewTiger(false)
              if (availableTigers.length > 0) {
                setTigerCode(availableTigers[0].code)
                setTigerName(availableTigers[0].name || `Tiger ${availableTigers[0].code}`)
              }
            }}
            className={`flex-1 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
              !isNewTiger
                ? "bg-white text-ink-900 shadow-sm border border-ink-100"
                : "text-ink-500 hover:text-ink-900 hover:bg-page-100"
            }`}
          >
            Existing Catalogue Tiger ({availableTigers.length})
          </button>
          <button
            type="button"
            onClick={() => {
              setIsNewTiger(true)
              const nextNum = availableTigers.reduce((max, t) => {
                const num = parseInt(t.code.replace(/\D/g, "") || "0", 10)
                return num > max ? num : max
              }, 45) + 1
              setTigerCode(`T0${nextNum}`)
              setTigerName(`New Sub-Adult T0${nextNum}`)
            }}
            className={`flex-1 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
              isNewTiger
                ? "bg-white text-ink-900 shadow-sm border border-ink-100"
                : "text-ink-500 hover:text-ink-900 hover:bg-page-100"
            }`}
          >
            Spot New / Uncatalogued
          </button>
        </div>

        {/* Tiger Details */}
        {!isNewTiger ? (
          <div>
            <label className="block text-xs font-mono uppercase text-ink-900 font-bold mb-1.5 tracking-wider">
              Select Catalogue Tiger *
            </label>
            <select
              value={tigerCode}
              onChange={e => {
                const code = e.target.value
                setTigerCode(code)
                const found = availableTigers.find((t: any) => t.code === code)
                if (found) {
                  setTigerName(found.name || `Tiger ${code}`)
                  if ((found as any).sex) setTigerSex((found as any).sex)
                }
              }}
              className="w-full bg-white text-ink-900 border border-ink-100 rounded-xl px-3.5 py-2.5 text-xs font-mono focus:outline-none focus:border-forest-500 shadow-sm cursor-pointer"
            >
              {availableTigers.map((t) => (
                <option key={t.id || t.code} value={t.code} className="bg-white text-ink-900 py-1">
                  {t.code} • {t.name || `Tiger ${t.code}`} ({(t as any).sex || "UNKNOWN"})
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-2.5 bg-page-50 p-3 rounded-xl border border-ink-100">
            <div>
              <label className="block text-[10px] font-mono uppercase text-ink-900 font-bold mb-1">Tiger Code *</label>
              <input
                type="text"
                required
                placeholder="e.g. T048"
                value={tigerCode}
                onChange={e => setTigerCode(e.target.value.toUpperCase())}
                className="w-full bg-white text-ink-900 placeholder:text-ink-300 border border-ink-100 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold focus:outline-none focus:border-forest-500 shadow-sm"
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-ink-900 font-bold mb-1">Moniker / Name</label>
              <input
                type="text"
                placeholder="e.g. Rudra, Kalyani"
                value={tigerName}
                onChange={e => setTigerName(e.target.value)}
                className="w-full bg-white text-ink-900 placeholder:text-ink-300 border border-ink-100 rounded-lg px-2.5 py-1.5 text-xs font-mono focus:outline-none focus:border-forest-500 shadow-sm"
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase text-ink-900 font-bold mb-1">Sex</label>
              <select
                value={tigerSex}
                onChange={e => setTigerSex(e.target.value)}
                className="w-full bg-white text-ink-900 border border-ink-100 rounded-lg px-2 py-1.5 text-xs font-mono focus:outline-none focus:border-forest-500 shadow-sm"
              >
                <option value="MALE" className="bg-white text-ink-900">MALE</option>
                <option value="FEMALE" className="bg-white text-ink-900">FEMALE</option>
                <option value="UNKNOWN" className="bg-white text-ink-900">UNKNOWN</option>
              </select>
            </div>
          </div>
        )}

        {/* Location Name with Auto-detection */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-xs font-mono uppercase text-ink-900 font-bold tracking-wider">
              Spotting Location / Landmark *
            </label>
            <span className="text-[10px] font-mono text-emerald-700 font-bold flex items-center gap-1">
              <Sparkles size={11} className="text-emerald-600" /> Auto-Detects GPS
            </span>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              required
              placeholder="Type landmark (e.g. Alikatta Meadow, Bodhanala Lake)..."
              value={locationName}
              onChange={e => handleLocationChange(e.target.value)}
              className="flex-1 bg-white text-ink-900 placeholder:text-ink-300 border border-ink-100 rounded-xl px-3.5 py-2.5 text-xs font-mono focus:outline-none focus:border-forest-500 shadow-sm"
            />

            {/* Presets dropdown quick picker */}
            <select
              onChange={e => {
                if (e.target.value) handleLocationChange(e.target.value)
              }}
              className="bg-white text-ink-900 border border-ink-100 rounded-xl px-2.5 py-2 text-xs font-mono font-bold focus:outline-none focus:border-forest-500 cursor-pointer shadow-sm"
              defaultValue=""
            >
              <option value="" disabled className="bg-white text-ink-400">Quick Landmarks</option>
              {PENCH_PRESETS.map((p, i) => (
                <option key={i} value={p.name} className="bg-white text-ink-900 py-1">
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {autoDetectedBadge && (
            <p className="text-[11px] font-mono text-emerald-700 mt-1.5 flex items-center gap-1 font-semibold">
              <CheckCircle2 size={12} className="text-emerald-600" /> {autoDetectedBadge}
            </p>
          )}
        </div>

        {/* Real Coordinates Grid */}
        <div className="grid grid-cols-2 gap-3 bg-page-50 p-3 rounded-xl border border-ink-100">
          <div>
            <label className="block text-[10px] font-mono uppercase text-ink-600 font-bold mb-1">Latitude (° N)</label>
            <input
              type="number"
              step="0.0001"
              required
              value={latitude}
              onChange={e => setLatitude(parseFloat(e.target.value))}
              className="w-full bg-white text-ink-900 font-mono font-bold border border-ink-100 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-forest-500 shadow-sm"
            />
          </div>
          <div>
            <label className="block text-[10px] font-mono uppercase text-ink-600 font-bold mb-1">Longitude (° E)</label>
            <input
              type="number"
              step="0.0001"
              required
              value={longitude}
              onChange={e => setLongitude(parseFloat(e.target.value))}
              className="w-full bg-white text-ink-900 font-mono font-bold border border-ink-100 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-forest-500 shadow-sm"
            />
          </div>
        </div>

        {/* Behavior & Observation Notes */}
        <div>
          <label className="block text-xs font-mono uppercase text-ink-900 font-bold mb-1.5 tracking-wider">
            Observed Behavior & Field Notes *
          </label>
          <textarea
            required
            rows={2}
            placeholder="e.g. Walking along dirt road heading toward waterhole; peaceful demeanor..."
            value={behavior}
            onChange={e => setBehavior(e.target.value)}
            className="w-full bg-white text-ink-900 placeholder:text-ink-300 border border-ink-100 rounded-xl px-3.5 py-2 text-xs font-mono focus:outline-none focus:border-forest-500 shadow-sm"
          />
        </div>

        {/* Observer & Confidence Slider */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-mono uppercase text-ink-900 font-bold mb-1.5 tracking-wider">Observer Credential</label>
            <select
              value={observer}
              onChange={e => setObserver(e.target.value)}
              className="w-full bg-white text-ink-900 border border-ink-100 rounded-xl px-3 py-2 text-xs font-mono focus:outline-none focus:border-forest-500 shadow-sm"
            >
              <option value="GYPSY_NATURALIST" className="bg-white text-ink-900">Registered Gypsy Naturalist</option>
              <option value="FOREST_GUARD" className="bg-white text-ink-900">Forest Beat Guard Patrol</option>
              <option value="CAMERA_TRAP" className="bg-white text-ink-900">Telemetry Sensor / Camera Trap</option>
              <option value="TOURIST_GROUP" className="bg-white text-ink-900">Verified Tourist Report</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-mono uppercase text-ink-900 font-bold tracking-wider">Match Confidence</label>
              <span className="text-xs font-mono font-bold text-gold-500 bg-page-50 px-2 py-0.5 rounded border border-gold-400/30">{confidence}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="100"
              value={confidence}
              onChange={e => setConfidence(parseInt(e.target.value))}
              className="w-full accent-gold-500 cursor-pointer mt-1"
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            className="flex-1 text-xs uppercase border-ink-100 text-ink-600 hover:text-ink-900"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={submitting}
            className="flex-1 text-xs uppercase font-bold bg-forest-800 text-white hover:bg-forest-900 shadow-sm flex items-center justify-center gap-1.5"
          >
            <Send size={14} /> {submitting ? "Saving to PostgreSQL..." : "Plot Sighting on Map"}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}

export default SpotTigerModal
