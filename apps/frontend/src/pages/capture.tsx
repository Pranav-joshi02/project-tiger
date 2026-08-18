import React, { useRef, useState, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import Webcam from "react-webcam"
import {
  Camera,
  Scan,
  UploadCloud,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  FileImage,
  ShieldAlert,
  ShieldCheck,
  Zap,
  RotateCcw,
  Sparkles,
  Layers,
  Award,
  ArrowRight,
} from "lucide-react"
import { Card } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { api } from "../lib/api"
import { LiveCaptureResult } from "../lib/types"

// Synthetic preview sample images
const SAMPLE_TIGER_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%23d97706"/><g fill="%2318181b"><polygon points="100,50 120,200 80,350 110,350 140,200 120,50"/><polygon points="180,40 200,180 170,360 195,360 220,180 200,40"/><polygon points="260,60 280,220 250,370 275,370 300,220 280,60"/><polygon points="340,50 360,190 330,350 355,350 380,190 360,50"/><polygon points="420,70 440,210 410,360 435,360 460,210 440,70"/><polygon points="500,40 520,180 490,340 515,340 540,180 520,40"/></g><circle cx="150" cy="120" r="18" fill="%23fef08a"/><circle cx="152" cy="120" r="8" fill="%23000000"/><text x="220" y="380" font-family="monospace" font-size="20" fill="%23ffffff" font-weight="bold">PENCH TIGER T017 (BAGHIRA)</text></svg>`
const SAMPLE_ELEPHANT_NATURAL_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%231e293b"/><ellipse cx="320" cy="230" rx="170" ry="120" fill="%2364748b"/><circle cx="180" cy="190" r="90" fill="%2364748b"/><path d="M 140 220 Q 90 280 120 340 Q 145 350 140 320 Q 120 270 160 240 Z" fill="%2364748b"/><path d="M 120 310 Q 100 330 110 350 Q 130 350 130 330 Z" fill="%23ffffff"/><ellipse cx="230" cy="170" rx="40" ry="70" fill="%23475569"/><rect x="200" y="290" width="35" height="90" rx="10" fill="%23475569"/><rect x="260" y="290" width="35" height="90" rx="10" fill="%23475569"/><rect x="360" y="290" width="35" height="90" rx="10" fill="%23475569"/><rect x="420" y="290" width="35" height="90" rx="10" fill="%23475569"/><circle cx="160" cy="160" r="7" fill="%23000000"/><text x="140" y="385" font-family="monospace" font-size="16" fill="%23f8fafc" font-weight="bold">ASIAN ELEPHANT (ELEPHAS MAXIMUS)</text></svg>`
const SAMPLE_ELEPHANT_STRIPED_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%23334155"/><ellipse cx="320" cy="230" rx="170" ry="120" fill="%23d97706"/><circle cx="180" cy="190" r="90" fill="%23d97706"/><path d="M 140 220 Q 90 280 120 340 Q 145 350 140 320 Q 120 270 160 240 Z" fill="%23d97706"/><path d="M 120 310 Q 100 330 110 350 Q 130 350 130 330 Z" fill="%23ffffff"/><ellipse cx="230" cy="170" rx="40" ry="70" fill="%23b45309"/><rect x="200" y="290" width="35" height="90" rx="10" fill="%23b45309"/><rect x="260" y="290" width="35" height="90" rx="10" fill="%23b45309"/><rect x="360" y="290" width="35" height="90" rx="10" fill="%23b45309"/><rect x="420" y="290" width="35" height="90" rx="10" fill="%23b45309"/><g fill="%2318181b"><polygon points="220,130 230,220 215,220"/><polygon points="270,120 285,240 265,240"/><polygon points="320,115 335,250 315,250"/><polygon points="370,120 385,240 365,240"/><polygon points="420,135 435,230 415,230"/><polygon points="170,120 180,180 165,180"/></g><circle cx="160" cy="160" r="7" fill="%23000000"/><text x="110" y="385" font-family="monospace" font-size="16" fill="%23f8fafc" font-weight="bold">ELEPHANT (WITH TIGER STRIPE PATTERN)</text></svg>`
const SAMPLE_PERSON_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%231e293b"/><circle cx="300" cy="150" r="70" fill="%23fed7aa"/><rect x="200" y="240" width="200" height="160" rx="30" fill="%230f766e"/><polygon points="300,240 285,320 300,340 315,320" fill="%23dc2626"/><text x="170" y="380" font-family="monospace" font-size="20" fill="%23cbd5e1">RANGER / OBSERVER</text></svg>`
const SAMPLE_BLANK_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%23064e3b"/><path d="M 50 400 L 150 150 L 250 400 Z" fill="%23065f46"/><path d="M 200 400 L 320 100 L 450 400 Z" fill="%23047857"/><path d="M 380 400 L 480 180 L 580 400 Z" fill="%23065f46"/><text x="160" y="360" font-family="monospace" font-size="20" fill="%23a7f3d0">FOREST FOLIAGE (BLANK)</text></svg>`

export const CapturePage: React.FC = () => {
  const navigate = useNavigate()
  const webcamRef = useRef<Webcam>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [activeTab, setActiveTab] = useState<"camera" | "upload">("upload")
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string>("tiger_capture.jpg")
  const [status, setStatus] = useState<"IDLE" | "PROCESSING" | "COMPLETE" | "ERROR">("IDLE")
  const [result, setResult] = useState<LiveCaptureResult | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const captureCamera = useCallback(() => {
    const screenshot = webcamRef.current?.getScreenshot()
    if (screenshot) {
      setImageSrc(screenshot)
      setFileName("webcam_capture.jpg")
      setStatus("IDLE")
      setResult(null)
    }
  }, [webcamRef])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setFileName(file.name)
      const reader = new FileReader()
      reader.onload = (event) => {
        setImageSrc(event.target?.result as string)
        setStatus("IDLE")
        setResult(null)
      }
      reader.readAsDataURL(file)
    }
  }

  const loadSample = (type: "tiger" | "elephant_natural" | "elephant_striped" | "person" | "blank") => {
    if (type === "tiger") {
      setImageSrc(SAMPLE_TIGER_SVG)
      setFileName("tiger_t017_baghira.jpg")
    } else if (type === "elephant_natural") {
      setImageSrc(SAMPLE_ELEPHANT_NATURAL_SVG)
      setFileName("asian_elephant.jpg")
    } else if (type === "elephant_striped") {
      setImageSrc(SAMPLE_ELEPHANT_STRIPED_SVG)
      setFileName("asian_elephant_with_tiger_stripes.jpg")
    } else if (type === "person") {
      setImageSrc(SAMPLE_PERSON_SVG)
      setFileName("ranger_person_sample.jpg")
    } else {
      setImageSrc(SAMPLE_BLANK_SVG)
      setFileName("forest_foliage_blank.jpg")
    }
    setStatus("IDLE")
    setResult(null)
  }

  const retake = () => {
    setImageSrc(null)
    setStatus("IDLE")
    setResult(null)
    setErrorMessage(null)
  }

  const runAnalysis = async () => {
    if (!imageSrc) return
    setStatus("PROCESSING")
    setErrorMessage(null)

    try {
      // Convert data URL / imageSrc to Blob
      const res = await fetch(imageSrc)
      const blob = await res.blob()

      const captureResult = await api.uploadLiveCapture(blob, fileName)
      setResult(captureResult)
      setStatus("COMPLETE")
    } catch (err: any) {
      console.error("Live analysis failed:", err)
      setErrorMessage(err.message || "Failed to analyze image. Ensure backend is running.")
      setStatus("ERROR")
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-ink-100 pb-4">
        <div>
          <h2 className="text-3xl font-black font-serif text-ink-900 tracking-wide uppercase flex items-center gap-3">
            <Zap className="text-gold-400 animate-pulse" size={28} />
            Live Intelligence Uplink
          </h2>
          <p className="text-ink-500 font-mono text-xs mt-1">
            Real-time species verification gate · Flank extraction · Fast Tiger Re-ID Matching
          </p>
        </div>

        {/* Quick Sample Selectors */}
        <div className="flex items-center gap-2 bg-page-50 p-1.5 rounded-lg border border-ink-100 flex-wrap">
          <span className="text-[10px] font-mono uppercase text-ink-500 px-2">Quick Test:</span>
          <button
            onClick={() => loadSample("tiger")}
            className="px-2.5 py-1 text-xs font-semibold rounded-full bg-white text-ink-900 border border-ink-100 hover:border-gold-400 transition-colors"
          >
            Tiger
          </button>
          <button
            onClick={() => loadSample("elephant_natural")}
            className="px-2.5 py-1 text-xs font-semibold rounded-full bg-white text-ink-900 border border-ink-100 hover:border-gold-400 transition-colors"
          >
            Elephant
          </button>
          <button
            onClick={() => loadSample("elephant_striped")}
            className="px-2.5 py-1 text-xs font-semibold rounded-full bg-white text-ink-900 border border-ink-100 hover:border-gold-400 transition-colors"
          >
            Elephant (Striped)
          </button>
          <button
            onClick={() => loadSample("person")}
            className="px-2.5 py-1 text-xs font-semibold rounded-full bg-white text-ink-900 border border-ink-100 hover:border-gold-400 transition-colors"
          >
            Person
          </button>
          <button
            onClick={() => loadSample("blank")}
            className="px-2.5 py-1 text-xs font-semibold rounded-full bg-white text-ink-900 border border-ink-100 hover:border-gold-400 transition-colors"
          >
            Blank
          </button>
        </div>
      </div>


      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Input Panel */}
        <Card className="flex flex-col border border-ink-100 bg-white shadow-card">
          {/* Mode Switcher Tabs */}
          <div className="flex items-center justify-between border-b border-ink-100 pb-3 mb-4">
            <div className="flex gap-2">
              <button
                onClick={() => { setActiveTab("upload"); retake() }}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold font-mono transition-all flex items-center gap-1.5 ${
                  activeTab === "upload"
                    ? "bg-gold-400 text-white shadow-md font-bold"
                    : "bg-page-50 text-ink-600 hover:text-ink-900 hover:bg-page-100"
                }`}
              >
                <FileImage size={14} /> Upload Image
              </button>
              <button
                onClick={() => { setActiveTab("camera"); retake() }}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold font-mono transition-all flex items-center gap-1.5 ${
                  activeTab === "camera"
                    ? "bg-gold-400 text-white shadow-md font-bold"
                    : "bg-page-50 text-ink-600 hover:text-ink-900 hover:bg-page-100"
                }`}
              >
                <Camera size={14} /> Live Camera
              </button>
            </div>

            {status === "PROCESSING" && (
              <span className="flex items-center gap-2 text-xs font-mono text-gold-500 animate-pulse">
                <RefreshCw size={14} className="animate-spin" /> ANALYZING INFERENCE
              </span>
            )}
          </div>

          {/* Viewport Area */}
          <div className="flex-1 relative aspect-video bg-page-50 rounded-xl overflow-hidden border border-ink-100 flex items-center justify-center">
            {activeTab === "camera" ? (
              !imageSrc ? (
                <>
                  <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 pointer-events-none border-2 border-dashed border-gold-400/50 m-6 rounded-lg" />
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <Scan size={56} className="text-gold-400/50 animate-pulse" />
                  </div>
                </>
              ) : (
                <img src={imageSrc} className="w-full h-full object-contain" alt="Captured Frame" />
              )
            ) : (
              !imageSrc ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full h-full flex flex-col items-center justify-center p-6 border-2 border-dashed border-ink-200 hover:border-gold-400 rounded-xl cursor-pointer transition-colors bg-page-50"
                >
                  <UploadCloud size={48} className="text-gold-400 mb-3 animate-bounce" />
                  <p className="text-sm font-bold text-ink-900">Click to upload tiger or test photo</p>
                  <p className="text-xs text-ink-500 mt-1 font-mono">Supports JPG, PNG, WEBP</p>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept="image/*"
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="relative w-full h-full">
                  <img src={imageSrc} className="w-full h-full object-contain" alt="Selected Preview" />
                  <div className="absolute top-2 left-2 bg-white/90 px-2 py-1 rounded text-[10px] font-mono text-ink-900 shadow-sm border border-ink-100">
                    {fileName}
                  </div>
                </div>
              )
            )}
          </div>

          {/* Action Buttons */}
          <div className="mt-5 flex gap-3">
            {activeTab === "camera" && !imageSrc && (
              <Button onClick={captureCamera} className="flex-1 uppercase font-bold tracking-widest text-xs h-12 bg-gold-400 text-white hover:bg-gold-500">
                <Camera size={16} className="mr-2" /> Capture Frame
              </Button>
            )}

            {imageSrc && (
              <>
                <Button
                  variant="outline"
                  onClick={retake}
                  disabled={status === "PROCESSING"}
                  className="flex-1 text-xs uppercase font-mono border-ink-200 hover:border-ink-300 text-ink-900"
                >
                  <RotateCcw size={14} className="mr-2" /> Retake / Clear
                </Button>
                <Button
                  onClick={runAnalysis}
                  disabled={status === "PROCESSING"}
                  className="flex-1 text-xs uppercase font-bold tracking-wider h-12 bg-forest-500 hover:bg-forest-600 text-white shadow-lg"
                >
                  {status === "PROCESSING" ? (
                    <>
                      <RefreshCw size={16} className="mr-2 animate-spin" /> Verifying...
                    </>
                  ) : (
                    <>
                      <Zap size={16} className="mr-2" /> Analyze Pipeline
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </Card>

        {/* Right Column: Multi-Stage Analysis Result Card */}
        <Card className="flex flex-col border border-ink-100 bg-white shadow-card">
          <div className="border-b border-ink-100 pb-3 mb-4 flex items-center justify-between">
            <h3 className="font-serif font-bold text-lg text-ink-900 flex items-center gap-2">
              <Sparkles size={18} className="text-gold-400" /> Intelligence Output
            </h3>
            {result && (
              <span className="text-[11px] font-mono text-ink-500">
                Latency: <span className="text-forest-600 font-bold">{result.duration_ms}ms</span>
              </span>
            )}
          </div>

          <div className="flex-1 flex flex-col justify-center items-center p-6 text-center bg-page-50 rounded-xl border border-ink-100 min-h-[380px]">
            {status === "IDLE" && (
              <div className="space-y-3">
                <Scan size={52} className="text-ink-400 mx-auto animate-pulse" />
                <h4 className="text-sm font-bold text-ink-900 font-mono">READY FOR INGESTION</h4>
                <p className="text-xs text-ink-600 max-w-sm">
                  Upload an image or capture a webcam frame to trigger real-time species triage and Tiger Re-ID matching.
                </p>
              </div>
            )}

            {status === "PROCESSING" && (
              <div className="space-y-4 py-8">
                <RefreshCw size={52} className="text-gold-400 mx-auto animate-spin" />
                <div>
                  <h4 className="text-base font-bold text-gold-500 font-serif">EXECUTING MULTI-STAGE PIPELINE</h4>
                  <p className="text-xs text-ink-500 font-mono mt-1">
                    Stage 1: Species Triage → Stage 2: Flank Segmentation → Stage 3: Re-ID Matching
                  </p>
                </div>
                <div className="w-48 h-1.5 bg-ink-100 rounded-full mx-auto overflow-hidden">
                  <div className="w-full h-full bg-gold-400 animate-pulse" />
                </div>
              </div>
            )}

            {status === "COMPLETE" && result && (
              <div className="w-full text-left space-y-5 animate-fade-in">
                {/* Stage 1: Triage Header Banner */}
                {result.is_tiger ? (
                  <div className="p-4 bg-white border border-forest-500/20 rounded-xl flex items-start gap-3.5 shadow-sm">
                    <ShieldCheck size={28} className="text-forest-600 shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-forest-600 uppercase tracking-wider flex items-center gap-1.5">
                          Stage 1 · Verified Tiger
                        </span>
                        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-black bg-forest-50 text-forest-700 border border-forest-200">
                          {(result.triage_confidence * 100).toFixed(1)}% Confidence
                        </span>
                      </div>
                      <h4 className="text-lg font-black text-ink-900 font-serif mt-0.5">{result.species_name}</h4>
                      <p className="text-xs text-ink-600 mt-1">
                        Bengal Tiger verified. Pipeline automatically proceeded with flank feature extraction & individual catalog matching.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-white border border-gold-400/40 rounded-xl flex items-start gap-3.5 shadow-sm">
                    <ShieldAlert size={28} className="text-gold-500 shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-gold-600 uppercase tracking-wider flex items-center gap-1.5">
                          Stage 1 · Quarantined (Non-Tiger Wildlife)
                        </span>
                        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-black bg-gold-50 text-gold-700 border border-gold-200">
                          {(result.triage_confidence * 100).toFixed(1)}% Confidence
                        </span>
                      </div>
                      <h4 className="text-lg font-black text-ink-900 font-serif mt-0.5">{result.species_name}</h4>
                      <p className="text-xs text-ink-600 mt-1">
                        {result.message}
                      </p>
                    </div>
                  </div>
                )}

                {/* Metrics Breakdown Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div className="bg-white p-3 rounded-lg border border-ink-100 shadow-sm">
                    <span className="block text-[10px] text-ink-500 uppercase font-mono mb-1">Triage Classification</span>
                    <span className={`font-mono text-sm font-black ${result.is_tiger ? "text-forest-600" : "text-gold-600"}`}>
                      {result.triage_category.toUpperCase()}
                    </span>
                  </div>

                  <div className="bg-white p-3 rounded-lg border border-ink-100 shadow-sm">
                    <span className="block text-[10px] text-ink-500 uppercase font-mono mb-1">Triage Confidence</span>
                    <span className="font-mono text-sm font-black text-forest-600">
                      {(result.triage_confidence * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="bg-white p-3 rounded-lg border border-ink-100 shadow-sm col-span-2 sm:col-span-1">
                    <span className="block text-[10px] text-ink-500 uppercase font-mono mb-1">Pipeline Stage</span>
                    <span className="font-mono text-xs font-bold text-ink-900">
                      {result.is_tiger ? "STAGE 3 (COMPLETE)" : "STAGE 1 (HALTED)"}
                    </span>
                  </div>
                </div>

                {/* Stage 2 & 3: Tiger Re-ID Individual Match Details */}
                {result.is_tiger && result.reid && (
                  <div className="p-4 bg-white border border-gold-400 rounded-xl space-y-4 shadow-md">
                    <div className="flex items-center justify-between border-b border-ink-100 pb-3">
                      <div className="flex items-center gap-2">
                        <Award className="text-gold-500" size={20} />
                        <h4 className="font-serif font-black text-base text-ink-900">
                          Identity Match: <span className="text-gold-600">{result.reid.tiger_code} · {result.reid.tiger_name}</span>
                        </h4>
                      </div>
                      {result.reid.is_same_image && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-page-100 text-ink-700 border border-ink-200">
                          SAME TIGER DETECTED (CACHED)
                        </span>
                      )}
                    </div>

                    {/* Prominent Match Confidence Bar */}
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-ink-600">Re-ID Match Confidence</span>
                        <span className="font-bold text-forest-600">
                          {(result.reid.match_confidence * 100).toFixed(1)}% Match
                        </span>
                      </div>
                      <div className="w-full h-2.5 bg-page-100 rounded-full overflow-hidden border border-ink-100">
                        <div
                          className="h-full bg-forest-500 transition-all duration-700"
                          style={{ width: `${Math.min(100, Math.max(10, result.reid.match_confidence * 100))}%` }}
                        />
                      </div>
                    </div>

                    {/* Flank and Habitat info */}
                    <div className="grid grid-cols-3 gap-2 text-xs font-mono pt-1">
                      <div className="bg-page-50 p-2 rounded border border-ink-100">
                        <span className="text-[9px] text-ink-500 block uppercase">Flank View</span>
                        <span className="font-bold text-ink-900">{result.flank?.side || "LEFT"}</span>
                      </div>
                      <div className="bg-page-50 p-2 rounded border border-ink-100">
                        <span className="text-[9px] text-ink-500 block uppercase">Territory</span>
                        <span className="font-bold text-ink-900">{result.reid.territory_zone || "CORE"}</span>
                      </div>
                      <div className="bg-page-50 p-2 rounded border border-ink-100">
                        <span className="text-[9px] text-ink-500 block uppercase">Observations</span>
                        <span className="font-bold text-ink-900">{result.reid.total_observations || 1}</span>
                      </div>
                    </div>

                    {/* Candidate Matches */}
                    {result.reid.candidates && result.reid.candidates.length > 0 && (
                      <div className="border-t border-ink-100 pt-3">
                        <span className="text-[10px] font-mono text-ink-500 uppercase block mb-2">
                          Top Catalogue Candidates
                        </span>
                        <div className="space-y-1.5">
                          {result.reid.candidates.map((c, i) => (
                            <div key={i} className="flex justify-between items-center bg-page-50 border border-ink-50 px-3 py-1.5 rounded text-xs">
                              <span className="font-bold text-ink-900">
                                {c.tiger_code} <span className="text-ink-600 font-normal">({c.name})</span>
                              </span>
                              <span className="font-mono text-forest-600 font-bold">
                                {(c.similarity * 100).toFixed(1)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Review in Queue Action Button */}
                    <div className="pt-2 border-t border-ink-100">
                      <Button
                        onClick={() => navigate("/review")}
                        className="w-full text-xs font-mono uppercase font-bold py-3 bg-gold-400 text-white hover:bg-gold-500 shadow-sm flex items-center justify-center gap-2"
                      >
                        <ShieldCheck size={16} /> Review in Verification Queue <ArrowRight size={15} />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {status === "ERROR" && (
              <div className="space-y-3 py-6">
                <AlertTriangle size={52} className="text-red-500 mx-auto" />
                <h4 className="text-base font-bold text-red-600 font-mono">PIPELINE ERROR</h4>
                <p className="text-xs text-ink-700 max-w-sm">
                  {errorMessage || "Failed to process image through pipeline."}
                </p>
                <Button variant="outline" onClick={retake} className="text-xs mt-3 border-ink-200 text-ink-900">
                  Try Again
                </Button>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
export default CapturePage
