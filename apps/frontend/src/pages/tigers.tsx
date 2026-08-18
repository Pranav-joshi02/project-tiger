import React, { useEffect, useState } from "react"
import { api } from "../lib/api"
import { Tiger } from "../lib/types"
import { Card } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Eye, MapPin, Calendar, PlusCircle, RefreshCw, Sparkles, Search, ShieldCheck, Crosshair, CheckCircle2, AlertCircle } from "lucide-react"
import { Dialog } from "../components/ui/dialog"
import SpotTigerModal from "../components/map/spot-tiger-modal"

export const TigersPage: React.FC = () => {
  const [tigers, setTigers] = useState<Tiger[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [selectedTiger, setSelectedTiger] = useState<Tiger | null>(null)
  const [searchTerm, setSearchTerm] = useState<string>("")
  const [showEnrollModal, setShowEnrollModal] = useState<boolean>(false)
  const [newCode, setNewCode] = useState<string>("")
  const [newName, setNewName] = useState<string>("")
  const [newSex, setNewSex] = useState<string>("UNKNOWN")
  const [newNotes, setNewNotes] = useState<string>("")
  const [enrolling, setEnrolling] = useState<boolean>(false)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  // Spot Tiger Modal
  const [showSpotModal, setShowSpotModal] = useState<boolean>(false)
  const [spotTigerInitial, setSpotTigerInitial] = useState<any>(null)

  const fetchTigers = async () => {
    setLoading(true)
    try {
      const data = await api.getTigers()
      setTigers(data)
    } catch (err) {
      console.error("Failed to load tigers:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTigers()
  }, [])

  const handleManualEnroll = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCode.trim()) return

    setEnrolling(true)
    try {
      const created = await api.enrollTiger({
        code: newCode.trim().toUpperCase(),
        name: newName.trim() || undefined,
        sex: newSex,
        notes: newNotes.trim() || undefined,
      })

      setToastMessage(`Successfully enrolled new tiger ${created.code} (${created.name})`)
      setShowEnrollModal(false)
      setNewCode("")
      setNewName("")
      setNewNotes("")
      fetchTigers()
      setTimeout(() => setToastMessage(null), 4000)
    } catch (err: any) {
      console.error("Enrollment failed:", err)
      setToastMessage(`Error: ${err.message || "Failed to enroll tiger"}`)
      setTimeout(() => setToastMessage(null), 4000)
    } finally {
      setEnrolling(false)
    }
  }

  const handleSpotFromCard = (tiger: Tiger) => {
    setSpotTigerInitial({
      lat: 21.7432,
      lng: 79.3215,
      nearestLandmark: "Alikatta Central Meadow"
    })
    setShowSpotModal(true)
  }

  const filteredTigers = tigers.filter(
    (t) =>
      t.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.name && t.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (t.notes && t.notes.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-ink-100 pb-4">
        <div>
          <h2 className="font-serif font-black text-2xl text-ink-900 uppercase tracking-wide flex items-center gap-2.5">
            <ShieldCheck className="text-gold-400" size={26} />
            Tiger Identity Catalogue
          </h2>
          <p className="text-xs text-ink-500 font-mono mt-0.5">
            Listing all confirmed and provisional individual tigers enrolled in Pench Tiger Reserve database
          </p>
        </div>

        <div className="flex items-center gap-3">
          {toastMessage && (
            <div className={`px-3.5 py-1.5 rounded-lg text-xs font-mono animate-fade-in shadow-sm flex items-center gap-1.5 ${toastMessage.startsWith("Error") ? "bg-red-50 text-red-700 border border-red-200" : "bg-emerald-50 text-emerald-700 border border-emerald-200"}`}>
              {toastMessage.startsWith("Error") ? <AlertCircle size={14} /> : <CheckCircle2 size={14} />}
              {toastMessage}
            </div>
          )}

          <Button
            variant="outline"
            onClick={fetchTigers}
            className="text-xs font-mono text-ink-600 hover:text-ink-900 border-ink-100"
          >
            <RefreshCw size={13} className={`mr-1.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>

          <Button
            variant="primary"
            onClick={() => {
              const maxNum = tigers.reduce((max, t) => {
                const num = parseInt(t.code.replace(/\D/g, "") || "0", 10)
                return num > max ? num : max
              }, 45)
              setNewCode(`T0${maxNum + 1}`)
              setShowEnrollModal(true)
            }}
            className="text-xs font-mono uppercase font-bold bg-forest-800 text-white hover:bg-forest-900 shadow-sm"
          >
            <PlusCircle size={14} className="mr-1.5" /> Enroll New Tiger
          </Button>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="flex items-center gap-4 bg-white p-3 rounded-xl border border-ink-100 shadow-sm">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gold-400" />
          <input
            type="text"
            placeholder="Search catalogue by tiger code (e.g. T017), moniker, or territory notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-page-50 text-ink-900 placeholder:text-ink-400 border border-ink-100 rounded-lg pl-9 pr-4 py-2 text-xs focus:outline-none focus:border-forest-500 font-mono"
          />
        </div>
        <span className="text-xs font-mono text-ink-600 shrink-0">
          Showing <span className="text-gold-500 font-bold">{filteredTigers.length}</span> of {tigers.length} Individuals
        </span>
      </div>

      {/* Grid of Tiger cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-[260px] bg-page-50 rounded-xl border border-ink-100 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {filteredTigers.map((t) => {
            return (
              <Card
                key={t.id}
                className="relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300 flex flex-col justify-between h-[280px] border border-ink-100 bg-white shadow-card"
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-mono text-sm font-bold text-gold-500 px-2.5 py-0.5 rounded bg-page-50 border border-ink-100">
                      {t.code}
                    </span>
                    <span
                      className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                        t.status === "CONFIRMED"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-amber-50 text-amber-700 border-amber-200"
                      }`}
                    >
                      {t.status}
                    </span>
                  </div>

                  <h3 className="font-serif text-2xl font-bold text-ink-900 mt-1 mb-1.5">
                    {t.name || `Tiger ${t.code}`}
                  </h3>

                  <p className="text-xs text-ink-500 line-clamp-3 leading-relaxed">
                    {t.notes || "Resident tiger catalogued in Pench telemetry records."}
                  </p>
                </div>

                <div className="border-t border-ink-100 pt-3 mt-3 flex items-center justify-between text-xs text-ink-500">
                  <span className="font-mono text-[11px] text-emerald-700 font-semibold">
                    {t.total_observations || 1} Sightings Recorded
                  </span>

                  <div className="flex items-center gap-1.5">
                    <Button
                      variant="outline"
                      className="text-[10px] uppercase font-mono px-2.5 py-1.5 gap-1 border-ink-100 hover:border-forest-500 text-gold-500 hover:text-forest-800"
                      onClick={() => handleSpotFromCard(t)}
                    >
                      <Crosshair size={11} /> Spot
                    </Button>

                    <Button
                      variant="outline"
                      className="text-[10px] uppercase font-mono px-2.5 py-1.5 gap-1 border-ink-100 hover:border-forest-500 text-ink-600"
                      onClick={() => setSelectedTiger(t)}
                    >
                      Profile <Eye size={11} />
                    </Button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Details Dialog */}
      <Dialog
        isOpen={!!selectedTiger}
        onClose={() => setSelectedTiger(null)}
        title={`Catalogue Profile: ${selectedTiger?.code || ""}`}
      >
        {selectedTiger && (
          <div className="space-y-4 text-ink-600">
            <div className="text-center pb-3 border-b border-ink-100">
              <div className="w-16 h-16 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center mx-auto mb-2 shadow-sm text-emerald-600">
                <ShieldCheck size={32} />
              </div>
              <h3 className="font-serif text-2xl font-black text-ink-900">{selectedTiger.name || "Unnamed"}</h3>
              <p className="text-xs text-gold-500 font-mono uppercase tracking-widest mt-0.5">
                {selectedTiger.code} · Status: {selectedTiger.status}
              </p>
            </div>

            <div className="space-y-2.5 text-sm surface-inset p-4 rounded-xl border border-ink-100">
              <div className="flex justify-between">
                <span className="text-ink-500 font-mono text-xs">Biological Sex</span>
                <span className="font-bold text-ink-900">{selectedTiger.sex}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-500 font-mono text-xs">Total Observations</span>
                <span className="font-bold text-emerald-700 font-mono">{selectedTiger.total_observations} Sightings</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-500 font-mono text-xs">First Sighting</span>
                <span className="font-mono text-xs text-ink-600">{selectedTiger.first_seen ? new Date(selectedTiger.first_seen).toLocaleDateString() : "N/A"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-500 font-mono text-xs">Last Verified</span>
                <span className="font-mono text-xs text-ink-600">{selectedTiger.last_seen ? new Date(selectedTiger.last_seen).toLocaleDateString() : "Active in Core"}</span>
              </div>
            </div>

            <div className="surface-inset p-4 rounded-xl border border-ink-100 text-xs">
              <h4 className="font-bold mb-1 text-gold-500 uppercase font-mono tracking-wider">Territory & Field Notes</h4>
              <p className="leading-relaxed text-ink-600">{selectedTiger.notes || "Resident tiger individual recorded in Pench telemetry database."}</p>
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                variant="outline"
                className="flex-1 text-xs uppercase text-gold-500 hover:text-gold-600 border-ink-100"
                onClick={() => {
                  handleSpotFromCard(selectedTiger)
                  setSelectedTiger(null)
                }}
              >
                <Crosshair size={13} className="mr-1" /> Spot on Real Map
              </Button>
              <Button
                variant="primary"
                className="flex-1 text-xs uppercase py-3 bg-forest-800 text-white font-bold hover:bg-forest-900 shadow-sm"
                onClick={() => setSelectedTiger(null)}
              >
                Close Profile
              </Button>
            </div>
          </div>
        )}
      </Dialog>

      {/* Manual Tiger Enrollment Modal */}
      <Dialog
        isOpen={showEnrollModal}
        onClose={() => setShowEnrollModal(false)}
        title="Manual Tiger Enrollment"
      >
        <form onSubmit={handleManualEnroll} className="space-y-4 text-ink-900">
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs">
            <p className="font-bold text-emerald-700 flex items-center gap-1.5 font-mono">
              <Sparkles size={14} /> Permanent Catalogue Registration
            </p>
            <p className="text-emerald-600 mt-0.5 text-[11px]">
              Registers a new tiger identity into the Pench PostgreSQL database.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-mono uppercase text-ink-900 font-bold mb-1 tracking-wider">
                Tiger Code *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. T046"
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                className="w-full bg-white text-ink-900 placeholder:text-ink-400 border border-ink-100 rounded-lg px-3.5 py-2 text-xs font-mono focus:outline-none focus:border-forest-500"
              />
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-ink-900 font-bold mb-1 tracking-wider">
                Sex
              </label>
              <select
                value={newSex}
                onChange={(e) => setNewSex(e.target.value)}
                className="w-full bg-white text-ink-900 border border-ink-100 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-forest-500"
              >
                <option value="UNKNOWN" className="bg-white text-ink-900">UNKNOWN</option>
                <option value="MALE" className="bg-white text-ink-900">MALE</option>
                <option value="FEMALE" className="bg-white text-ink-900">FEMALE</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-900 font-bold mb-1 tracking-wider">
              Tiger Name / Moniker
            </label>
            <input
              type="text"
              placeholder="e.g. Rudra, Veer, Kalyani"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full bg-white text-ink-900 placeholder:text-ink-400 border border-ink-100 rounded-lg px-3.5 py-2 text-xs font-mono focus:outline-none focus:border-forest-500"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-900 font-bold mb-1 tracking-wider">
              Field Notes / Territory
            </label>
            <textarea
              placeholder="Dominant territory, camera station range, physical markings..."
              value={newNotes}
              onChange={(e) => setNewNotes(e.target.value)}
              rows={3}
              className="w-full bg-white text-ink-900 placeholder:text-ink-400 border border-ink-100 rounded-lg px-3.5 py-2 text-xs font-mono focus:outline-none focus:border-forest-500"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowEnrollModal(false)}
              className="flex-1 text-xs uppercase border-ink-100 text-ink-600 hover:text-ink-900"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={enrolling}
              className="flex-1 text-xs uppercase font-bold bg-forest-800 text-white hover:bg-forest-900 shadow-sm"
            >
              {enrolling ? "Enrolling..." : "Enroll Tiger"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Spot Tiger Modal */}
      <SpotTigerModal
        isOpen={showSpotModal}
        onClose={() => setShowSpotModal(false)}
        initialCoords={spotTigerInitial}
        tigers={tigers}
        onSightingPlotted={(res) => {
          setToastMessage(`Plotted ${res.sighting.tiger_code} (${res.sighting.tiger_name}) at ${res.sighting.location_name}`)
          fetchTigers()
          setTimeout(() => setToastMessage(null), 4500)
        }}
      />
    </div>
  )
}

export default TigersPage
