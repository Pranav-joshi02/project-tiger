export interface MetricSummary {
  images_processed: number
  quarantined: number
  storage_saved_bytes: number
  known_individuals: number
  review_queue: number
}

export interface LatestRun {
  id: string | null
  name: string | null
  status: string | null
  total_images: number
  retained_images: number
  quarantined_images: number
  tiger_detections: number
  created_at: string | null
  completed_at: string | null
  duration_seconds: number | null
}

export interface Alert {
  id: string
  type: string
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string
  status: "ACTIVE" | "INVESTIGATING" | "ACKNOWLEDGED" | "RESOLVED" | "DISMISSED" | string
  title: string
  summary: string
  tiger_id?: string
  tiger_code?: string
  tiger_name?: string
  station_code?: string
  latitude?: number
  longitude?: number
  evidence_confidence?: number
  action_recommendation?: string
  created_at: string
}

export interface DashboardData {
  data_notice: string
  metrics: MetricSummary
  latest_run: LatestRun
  alerts: Alert[]
}

export interface Tiger {
  id: string
  code: string
  name: string | null
  sex: string
  status: string
  total_observations: number
  first_seen: string | null
  last_seen: string | null
  notes: string | null
}

export interface TigerLocation {
  id: string
  code: string
  name: string
  sex: "MALE" | "FEMALE" | "UNKNOWN"
  latitude: number
  longitude: number
  approx_zone: string
  current_activity: "PATROLLING" | "RESTING_WATERHOLE" | "HUNTING" | "TERRITORIAL_MARKING" | "WITH_CUBS" | "TRANSIT"
  last_seen_time: string
  last_seen_relative: string
  sighting_confidence: number
  territory_radius_km: number
  dominant_waterhole: string
  recent_coordinates?: { lat: number; lng: number }[]
  recommended_time_slot: string
  notes?: string
}

export interface SightseeingZone {
  id: string
  name: string
  zone_type: "CORE" | "BUFFER" | "CORRIDOR"
  latitude: number
  longitude: number
  radius_meters: number
  visibility_score_morning: number
  visibility_score_afternoon: number
  visibility_score_night: number
  primary_habitat: string
  description: string
  resident_tigers: { code: string; name: string; likelihood: number }[]
  key_landmarks: string[]
  recommended_gate: string
  best_safari_timing: string
  camera_stations_nearby: string[]
}

export interface SafariWaypoint {
  id: string
  name: string
  latitude: number
  longitude: number
  order: number
  type: "GATE" | "WATERHOLE" | "MEADOW" | "RIDGE" | "RIVERBED" | "CHECKPOST"
  tiger_sighting_chance: number
  description: string
}

export interface SafariRoute {
  id: string
  code: string
  name: string
  zone: "TOURIA" | "KARMAJHIRI" | "GUMTARA" | "KHURSAPAR" | "RUKHAD" | "JAMTARA"
  gate_name: string
  visibility_rating: number // 0-100%
  distance_km: number
  duration_hours: number
  terrain_difficulty: "EASY" | "MODERATE" | "RUGGED"
  slot_recommendation: "DAWN_SAFARI" | "DUSK_SAFARI" | "BOTH" | "NIGHT_BUFFER"
  max_vehicles: number
  current_vehicles_booked: number
  resident_tigers: string[]
  summary: string
  highlights: string[]
  naturalist_tips: string
  suggested_lens: string
  waypoints: SafariWaypoint[]
  recent_sightings_count_48h: number
}

export interface LiveSafariSighting {
  id: string
  route_id: string
  route_name: string
  tiger_code: string
  tiger_name: string
  location_name: string
  latitude: number
  longitude: number
  timestamp: string
  time_ago: string
  observed_by: "GYPSY_NATURALIST" | "CAMERA_TRAP" | "FOREST_GUARD" | "TOURIST_GROUP"
  behavior: string
  confidence_score: number
  photo_url?: string
}

export interface CameraStation {
  id: string
  code: string
  name: string
  latitude: number
  longitude: number
  zone: string
  status: string
  last_check: string | null
}

export interface ReviewCandidate {
  tiger_id?: string
  tiger_code: string
  name: string
  similarity: number
  status?: string
  notes?: string | null
  total_observations?: number
  last_seen?: string | null
  photo_url?: string | null
}

export interface ReviewItem {
  id: string
  state: string
  similarity_score: number | null
  candidates: ReviewCandidate[] | null
  suggested_tiger_id: string | null
  image_id?: string | null
  image_url?: string | null
  filename?: string | null
  flank_side?: string | null
  station_code?: string | null
  created_at: string
}

export interface FlankInfo {
  side: string
  quality_score: number
  bbox?: number[]
}

export interface ReidMatchCandidate {
  tiger_id?: string
  tiger_code: string
  name: string
  similarity: number
}

export interface ReidResult {
  match_status: "AUTO_MATCH" | "REVIEW_REQUIRED" | "NEW_TIGER"
  matched_tiger_id: string | null
  tiger_code: string
  tiger_name: string
  match_confidence: number
  is_same_image: boolean
  territory_zone?: string
  total_observations?: number
  candidates?: ReidMatchCandidate[]
}

export interface LiveCaptureResult {
  status: "TIGER_IDENTIFIED" | "NON_TIGER_HALTED" | "ERROR"
  is_tiger: boolean
  stage: string
  triage_category: string
  triage_confidence: number
  species_name: string
  message: string
  flank: FlankInfo | null
  reid: ReidResult | null
  run_id: string
  image_id?: string
  review_id?: string
  duration_ms: number
}
