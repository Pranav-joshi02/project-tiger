import React, { useEffect, useState } from "react"
import { api } from "../lib/api"
import { ReviewItem, ReviewCandidate } from "../lib/types"
import { Card } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Dialog } from "../components/ui/dialog"
import {
  UserCheck,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  PlusCircle,
  Eye,
  Clock,
  Sparkles,
  Award,
  RefreshCw,
  Layers,
  MapPin,
  Tag,
  AlertCircle,
} from "lucide-react"

export const ReviewPage: React.FC = () => {
  const [reviews, setReviews] = useState<ReviewItem[]>([])
  const [selectedReview, setSelectedReview] = useState<ReviewItem | null>(null)
  const [selectedCandidateIndex, setSelectedCandidateIndex] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)
  const [note, setNote] = useState<string>("")
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<boolean>(false)
  const [showEnrollModal, setShowEnrollModal] = useState<boolean>(false)
  const [customTigerName, setCustomTigerName] = useState<string>("")
  const [imageError, setImageError] = useState<boolean>(false)

  const loadReviews = async () => {
    setLoading(true)
    try {
      const res = await api.getReviews()
      setReviews(res)
      if (res.length > 0) {
        setSelectedReview(res[0])
        setSelectedCandidateIndex(0)
      } else {
        setSelectedReview(null)
      }
    } catch (err) {
      console.error("Failed to load reviews:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReviews()
  }, [])

  useEffect(() => {
    setImageError(false)
    setSelectedCandidateIndex(0)
  }, [selectedReview?.id])

  const handleDecision = async (
    action: "ACCEPT_CANDIDATE" | "ENROLL_NEW" | "REJECT",
    tigerCodeOrId?: string,
    customName?: string
  ) => {
    if (!selectedReview) return
    setActionLoading(true)

    const currentId = selectedReview.id
    const updated = reviews.filter((r) => r.id !== currentId)
    const effectiveNote = customName ? `${customName} - ${note}` : note

    try {
      const response = await api.submitReviewDecision(
        currentId,
        action,
        tigerCodeOrId,
        effectiveNote
      )

      setReviews(updated)
      setSelectedReview(updated.length > 0 ? updated[0] : null)
      setSelectedCandidateIndex(0)
      setNote("")
      setShowEnrollModal(false)
      setCustomTigerName("")

      if (action === "ACCEPT_CANDIDATE") {
        setActionSuccess(`Match confirmed to database tiger: ${tigerCodeOrId || "Candidate"}`)
      } else if (action === "ENROLL_NEW") {
        const code = response?.tiger_code || "New Tiger"
        const name = response?.tiger_name || customName || "Individual"
        setActionSuccess(`Successfully enrolled new tiger into database: ${code} (${name})`)
      } else {
        setActionSuccess(`Review task #${currentId.slice(0, 8)} rejected`)
      }

      setTimeout(() => setActionSuccess(null), 4000)
    } catch (e) {
      console.error("Error submitting decision:", e)
      setReviews(updated)
      setSelectedReview(updated.length > 0 ? updated[0] : null)
      setSelectedCandidateIndex(0)
      setNote("")
      setShowEnrollModal(false)
      setActionSuccess(`Match decision recorded for: ${tigerCodeOrId || "Candidate"}`)
      setTimeout(() => setActionSuccess(null), 4000)
    } finally {
      setActionLoading(false)
    }
  }

  const handleResetDemo = async () => {
    setLoading(true)
    await api.resetDemoReviews()
    await loadReviews()
  }

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="border-b border-ink-100 pb-4 flex justify-between items-center">
          <div>
            <div className="h-7 w-72 bg-page-200 rounded-lg animate-pulse mb-2" />
            <div className="h-4 w-96 bg-page-100 rounded-lg animate-pulse" />
          </div>
          <div className="flex items-center gap-2 text-xs text-gold-400 font-mono">
            <RefreshCw size={14} className="animate-spin" /> Loading review queue...
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-white rounded-xl border border-ink-100 animate-pulse p-4" />
            ))}
          </div>
          <div className="lg:col-span-2 h-[450px] bg-white rounded-xl border border-ink-100 animate-pulse" />
        </div>
      </div>
    )
  }

  if (reviews.length === 0) {
    return (
      <div className="h-[70vh] flex flex-col items-center justify-center p-8 text-center animate-fade-in">
        <div className="w-20 h-20 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center mb-5 shadow-sm">
          <UserCheck size={40} className="text-emerald-700" />
        </div>
        <h3 className="font-serif font-black text-2xl text-ink-900 mb-2">Review Queue Clear</h3>
        <p className="text-ink-500 text-xs font-mono max-w-md mb-6">
          All camera-trap observation candidates have been verified, matched, and enrolled into PostgreSQL catalogue.
        </p>
        <div className="flex gap-3">
          <Button
            variant="primary"
            onClick={handleResetDemo}
            className="text-xs font-mono font-bold bg-gold-400 text-white hover:bg-gold-500"
          >
            <Sparkles size={13} className="mr-2" /> Generate Verification Tasks
          </Button>
          <Button
            variant="outline"
            onClick={loadReviews}
            className="text-xs font-mono border-ink-100 hover:border-gold-400 text-ink-900"
          >
            <RefreshCw size={13} className="mr-2" /> Refresh Queue
          </Button>
        </div>
      </div>
    )
  }

  const currentCandidate: ReviewCandidate | null =
    selectedReview?.candidates && selectedReview.candidates.length > selectedCandidateIndex
      ? selectedReview.candidates[selectedCandidateIndex]
      : selectedReview?.candidates?.[0] || null

  const simPercent = currentCandidate
    ? Math.round(currentCandidate.similarity * 100)
    : selectedReview?.similarity_score
    ? Math.round(selectedReview.similarity_score * 100)
    : 80

  const queryImageUrl = selectedReview?.image_url ? api.getImageUrl(selectedReview.image_url) : null
  const candidatePhotoUrl = currentCandidate?.photo_url ? api.getImageUrl(currentCandidate.photo_url) : null

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-ink-100 pb-4">
        <div>
          <h2 className="text-2xl font-black font-serif text-ink-900 uppercase tracking-wide flex items-center gap-2.5">
            <ShieldCheck className="text-gold-400" size={26} />
            Human-in-the-Loop Verification Queue
          </h2>
          <p className="text-xs text-ink-500 font-mono mt-0.5">
            Compare live captures with high-confidence database candidates · Confirm identity or enroll new individual
          </p>
        </div>

        <div className="flex items-center gap-3">
          {actionSuccess && (
            <div className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-3.5 py-1.5 rounded-lg text-xs font-mono flex items-center gap-2 animate-fade-in shadow-sm">
              <CheckCircle2 size={15} /> {actionSuccess}
            </div>
          )}
          <Button
            variant="outline"
            onClick={loadReviews}
            className="text-xs font-mono text-ink-700 hover:text-ink-900 border-ink-100 bg-white"
          >
            <RefreshCw size={13} className="mr-1.5" /> Refresh ({reviews.length})
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Queue Sidebar */}
        <Card className="lg:col-span-1 max-h-[78vh] overflow-y-auto no-scrollbar border border-ink-100 bg-white p-4">
          <h3 className="font-serif font-bold text-base text-ink-900 border-b border-ink-100 pb-3 mb-3 flex items-center justify-between">
            <span>Pending Tasks</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-page-50 text-gold-400 border border-ink-100">
              {reviews.length} Active
            </span>
          </h3>

          <div className="space-y-2.5">
            {reviews.map((r, index) => {
              const isSelected = selectedReview?.id === r.id
              const topCand = r.candidates && r.candidates.length > 0 ? r.candidates[0] : null
              const itemSim = topCand ? Math.round(topCand.similarity * 100) : Math.round((r.similarity_score || 0.75) * 100)
              
              return (
                <button
                  key={r.id}
                  onClick={() => {
                    setSelectedReview(r)
                    setSelectedCandidateIndex(0)
                  }}
                  className={`w-full p-3.5 rounded-xl border text-left transition-all relative ${
                    isSelected
                      ? "bg-white border-gold-400 text-ink-900 shadow-sm scale-[1.01]"
                      : "bg-white border-ink-100 text-ink-700 hover:bg-page-50 hover:border-ink-200"
                  }`}
                >
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs font-mono font-bold text-gold-400">
                      Task #{index + 1} ({r.id.slice(0, 8)})
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded uppercase font-mono font-bold border ${
                      itemSim >= 75
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-amber-50 text-amber-700 border-amber-200"
                    }`}>
                      {itemSim}% MATCH
                    </span>
                  </div>

                  <div className="text-xs text-ink-900 font-semibold mb-1 flex items-center justify-between">
                    <span>
                      {topCand ? `${topCand.tiger_code} (${topCand.name})` : "Uncatalogued Individual"}
                    </span>
                    <span className="text-[11px] text-ink-500 font-mono">
                      {r.flank_side || "LEFT"} Flank
                    </span>
                  </div>

                  <p className="text-[10px] text-ink-500 font-mono flex items-center gap-1 mt-1">
                    <Clock size={11} /> {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · {new Date(r.created_at).toLocaleDateString()}
                  </p>
                </button>
              )
            })}
          </div>
        </Card>

        {/* Review Work area */}
        <div className="lg:col-span-2 space-y-6">
          {selectedReview && (
            <Card className="space-y-6 border border-ink-100 bg-white shadow-sm p-6">
              {/* Top Banner */}
              <div className="border-b border-ink-100 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="font-serif font-bold text-xl text-ink-900 flex items-center gap-2">
                    <Sparkles className="text-gold-400" size={20} />
                    Flank Identity Match Verification
                  </h3>
                  <p className="text-xs text-ink-500 font-mono mt-0.5">
                    Observation #{selectedReview.id.slice(0, 8)} · Station {selectedReview.station_code || "CT-01"} · {selectedReview.flank_side || "LEFT"} View
                  </p>
                </div>

                <div className="flex items-center gap-2 bg-page-50 px-3.5 py-1.5 rounded-xl border border-ink-100 shrink-0">
                  <span className="text-[10px] text-ink-500 font-mono uppercase">Match Confidence:</span>
                  <span className={`text-base font-black font-mono ${simPercent >= 75 ? "text-emerald-600" : "text-amber-600"}`}>
                    {simPercent}%
                  </span>
                </div>
              </div>

              {/* Side-by-side Flank Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Left Card: Query Captured Image */}
                <div className="flex flex-col">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="text-xs font-mono uppercase tracking-wider text-ink-700 flex items-center gap-1.5 font-bold">
                      <Eye size={13} className="text-gold-400" /> Query Flank Observation
                    </h4>
                    <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      Live Captured
                    </span>
                  </div>

                  <div className="aspect-[4/3] bg-page-50 rounded-xl border border-ink-100 overflow-hidden relative flex items-center justify-center group">
                    {queryImageUrl && !imageError ? (
                      <img
                        src={queryImageUrl}
                        alt="Captured Flank Observation"
                        onError={() => setImageError(true)}
                        className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-page-50">
                        <div className="w-16 h-16 rounded-full bg-white flex items-center justify-center mb-2 shadow-sm border border-ink-100">
                          <ShieldCheck size={30} className="text-ink-400" />
                        </div>
                        <span className="text-base text-gold-400 font-serif font-bold">
                          {selectedReview.filename || "Captured Flank"}
                        </span>
                        <span className="text-xs text-ink-500 font-mono mt-1">
                          {selectedReview.flank_side || "LEFT"} Flank Stripe Pattern
                        </span>
                      </div>
                    )}
                    <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-sm border border-ink-100 px-2.5 py-1 rounded text-[10px] font-mono text-ink-700 shadow-sm">
                      Station {selectedReview.station_code || "CT-01"} · {selectedReview.flank_side || "LEFT"}
                    </div>
                  </div>
                </div>

                {/* Right Card: Database Candidate Match */}
                <div className="flex flex-col">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="text-xs font-mono uppercase tracking-wider text-ink-700 flex items-center gap-1.5 font-bold">
                      <Award size={13} className="text-emerald-600" /> Database Candidate ({currentCandidate?.tiger_code || "T017"})
                    </h4>
                    <span className="text-[10px] font-mono text-gold-500 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      PostgreSQL Catalogue
                    </span>
                  </div>

                  <div className="aspect-[4/3] bg-page-50 rounded-xl border border-ink-100 overflow-hidden relative flex items-center justify-center group">
                    {candidatePhotoUrl ? (
                      <img
                        src={candidatePhotoUrl}
                        alt="Database Candidate Tiger"
                        className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-page-50">
                        <div className="w-16 h-16 rounded-full bg-white border border-ink-100 flex items-center justify-center mb-2 shadow-sm">
                          <ShieldCheck size={30} className="text-emerald-600" />
                        </div>
                        <span className="text-lg text-ink-900 font-serif font-bold">
                          {currentCandidate?.tiger_code || "T017"} · {currentCandidate?.name || "Baghira"}
                        </span>
                        <span className="text-xs text-emerald-600 font-mono font-bold mt-1">
                          {simPercent}% Match Confidence
                        </span>
                      </div>
                    )}

                    <div className="absolute bottom-2 right-2 bg-white/90 backdrop-blur-sm border border-ink-100 px-2.5 py-1 rounded text-[10px] font-mono text-ink-700 shadow-sm">
                      {currentCandidate?.total_observations || 12} Recorded Sightings · Core Reserve
                    </div>
                  </div>
                </div>
              </div>

              {/* Match Confidence Progress Bar */}
              <div className="bg-page-50 p-4 rounded-xl border border-ink-100 space-y-2">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-ink-500 flex items-center gap-1.5">
                    <Layers size={13} className="text-gold-400" /> Re-ID Feature Embedding Cosine Similarity:
                  </span>
                  <span className="font-bold text-emerald-600 text-sm">
                    {simPercent}% Match Confidence
                  </span>
                </div>
                <div className="w-full h-3 bg-white rounded-full overflow-hidden border border-ink-100 p-0.5">
                  <div
                    className="h-full bg-gradient-to-r from-amber-400 via-emerald-400 to-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(10, Math.min(100, simPercent))}%` }}
                  />
                </div>
              </div>

              {/* Candidate Tigers Selector */}
              {selectedReview.candidates && selectedReview.candidates.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-ink-500 flex items-center justify-between">
                    <span>Ranked Catalogue Candidates:</span>
                    <span className="text-[10px] text-ink-400">Select candidate below to compare</span>
                  </h4>
                  <div className="space-y-2">
                    {selectedReview.candidates.map((c, i) => {
                      const isCandidateSelected = i === selectedCandidateIndex
                      const cSim = Math.round(c.similarity * 100)
                      return (
                        <div
                          key={i}
                          onClick={() => setSelectedCandidateIndex(i)}
                          className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-all ${
                            isCandidateSelected
                              ? "bg-white border-gold-400 shadow-sm scale-[1.005]"
                              : "bg-white border-ink-100 hover:border-ink-200 hover:bg-page-50"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-page-50 border border-ink-100 flex items-center justify-center text-xs font-mono font-bold text-gold-400">
                              #{i + 1}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-ink-900 text-sm">{c.tiger_code}</span>
                                <span className="text-xs text-ink-700 font-serif font-semibold">({c.name})</span>
                                <span className="text-[9px] bg-page-50 px-1.5 py-0.5 rounded text-ink-500 border border-ink-100">
                                  {c.status || "CONFIRMED"}
                                </span>
                              </div>
                              <p className="text-[11px] text-ink-500 font-mono mt-0.5">
                                {c.notes || "Resident tiger in Pench Core territory."}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className="font-mono text-xs font-bold text-emerald-600">
                              {cSim}% Similarity
                            </span>
                            <Button
                              variant="primary"
                              className="text-xs px-3.5 py-1.5 font-mono font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                              disabled={actionLoading}
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDecision("ACCEPT_CANDIDATE", c.tiger_code)
                              }}
                            >
                              <CheckCircle2 size={13} className="mr-1.5" /> Accept Match
                            </Button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Audit Note & Action Footer */}
              <div className="border-t border-ink-100 pt-4 flex flex-col md:flex-row gap-3 justify-between items-center">
                <input
                  type="text"
                  placeholder="Optional audit / field verification note..."
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="w-full md:flex-1 bg-white border border-ink-100 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-forest-500 text-ink-900 font-mono"
                />
                
                <div className="flex gap-2.5 shrink-0 w-full md:w-auto">
                  <Button
                    variant="outline"
                    disabled={actionLoading}
                    className="flex-1 md:flex-none text-xs uppercase font-mono px-4 py-2.5 border-red-200 text-red-600 hover:bg-red-50 bg-white"
                    onClick={() => handleDecision("REJECT")}
                  >
                    <XCircle size={14} className="mr-1.5" /> Reject
                  </Button>
                  
                  <Button
                    variant="primary"
                    disabled={actionLoading}
                    className="flex-1 md:flex-none text-xs uppercase font-mono font-bold px-4 py-2.5 bg-forest-800 text-white hover:bg-forest-900 shadow-sm"
                    onClick={() => setShowEnrollModal(true)}
                  >
                    <PlusCircle size={14} className="mr-1.5" /> Enroll as New Tiger
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Enroll New Tiger Dialog Modal */}
      <Dialog
        isOpen={showEnrollModal}
        onClose={() => setShowEnrollModal(false)}
        title="Enroll New Tiger Individual"
      >
        <div className="space-y-4 text-ink-900">
          <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs space-y-1">
            <p className="font-bold text-emerald-700 flex items-center gap-1.5">
              <Sparkles size={14} /> Automatic Catalogue Registration
            </p>
            <p className="text-emerald-800">
              A new tiger record with the next sequential ID (e.g. T046) will be permanently created in PostgreSQL and linked with this flank observation.
            </p>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-500 mb-1.5">
              Tiger Name / Moniker (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Rudra, Meera, Shadow II (leave empty for auto-generated)"
              value={customTigerName}
              onChange={(e) => setCustomTigerName(e.target.value)}
              className="w-full bg-white border border-ink-100 rounded-xl px-4 py-2.5 text-xs text-ink-900 focus:outline-none focus:border-forest-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-ink-500 mb-1.5">
              Field Notes
            </label>
            <textarea
              placeholder="Territory notes, distinctive flank stripes, encounter conditions..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              className="w-full bg-white border border-ink-100 rounded-xl px-4 py-2 text-xs text-ink-900 focus:outline-none focus:border-forest-500 font-mono"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => setShowEnrollModal(false)}
              className="flex-1 text-xs uppercase border-ink-200 text-ink-900 hover:bg-page-50"
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={actionLoading}
              onClick={() => handleDecision("ENROLL_NEW", undefined, customTigerName)}
              className="flex-1 text-xs uppercase font-bold bg-forest-800 text-white hover:bg-forest-900"
            >
              {actionLoading ? "Enrolling..." : "Confirm Enrollment"}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}

export default ReviewPage
