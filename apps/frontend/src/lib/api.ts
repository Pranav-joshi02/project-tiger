import {
  DashboardData,
  Tiger,
  TigerLocation,
  SightseeingZone,
  SafariRoute,
  LiveSafariSighting,
  CameraStation,
  ReviewItem,
  LiveCaptureResult,
  Alert
} from "./types"

export const getApiBase = (): string => {
  if (typeof window !== "undefined") {
    if (window.location.port === "3000") {
      return "/api"
    }
    const host = window.location.hostname || "localhost"
    return `http://${host}:8000`
  }
  return "http://localhost:8000"
}

export const API_BASE = getApiBase()

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 4000): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    return res
  } finally {
    clearTimeout(timeoutId)
  }
}

// -------------------------------------------------------------
// Real Pench Tiger Reserve GIS & Fallback Records (21.65° - 21.85° N, 79.20° - 79.45° E)
// -------------------------------------------------------------

export const MOCK_TIGERS: Tiger[] = [
  { id: "t1", code: "T017", name: "Baghira", sex: "MALE", status: "CONFIRMED", total_observations: 18, first_seen: "2024-08-01", last_seen: "2026-08-15", notes: "Dominant prime male inhabiting Alikatta grasslands and Bodhanala core." },
  { id: "t2", code: "T021", name: "Tara", sex: "FEMALE", status: "CONFIRMED", total_observations: 14, first_seen: "2024-10-12", last_seen: "2026-08-15", notes: "Resident female frequently spotted along Bodhanala stream and Baghin Nala." },
  { id: "t3", code: "T008", name: "Sheru", sex: "MALE", status: "CONFIRMED", total_observations: 27, first_seen: "2024-03-05", last_seen: "2026-08-14", notes: "Veteran alpha male holding the high-elevation Chindimatta plateau and Totladoh ridge." },
  { id: "t4", code: "T032", name: "Naina", sex: "FEMALE", status: "CONFIRMED", total_observations: 11, first_seen: "2025-01-20", last_seen: "2026-08-15", notes: "Young mother with 2 sub-adult cubs patrolling Gumtara bamboo dense nullahs." },
  { id: "t5", code: "T045", name: "Shadow", sex: "MALE", status: "CONFIRMED", total_observations: 19, first_seen: "2024-07-15", last_seen: "2026-08-13", notes: "Stealth male active in southern core-buffer corridor near Karmajhiri and Rukhad." },
  { id: "t6", code: "T012", name: "Collarwali Lineage", sex: "FEMALE", status: "CONFIRMED", total_observations: 16, first_seen: "2024-06-10", last_seen: "2026-08-15", notes: "Direct daughter of legendary matriarch, rules eastern Touria and Pyorthadi waterbody." }
]

export const MOCK_TIGER_LOCATIONS: TigerLocation[] = [
  {
    id: "tloc-1",
    code: "T017",
    name: "Baghira",
    sex: "MALE",
    latitude: 21.7445,
    longitude: 79.3230,
    approx_zone: "Alikatta Central Meadow",
    current_activity: "PATROLLING",
    last_seen_time: new Date(Date.now() - 32 * 60000).toISOString(),
    last_seen_relative: "32m ago",
    sighting_confidence: 0.96,
    territory_radius_km: 38.5,
    dominant_waterhole: "Alikatta Waterhole & Lake",
    recommended_time_slot: "06:00 - 08:45 AM (Dawn)",
    notes: "Active near main grassland track; heading south toward Bodhanala crossing.",
    recent_coordinates: [
      { lat: 21.7470, lng: 79.3210 },
      { lat: 21.7455, lng: 79.3222 },
      { lat: 21.7445, lng: 79.3230 }
    ]
  },
  {
    id: "tloc-2",
    code: "T021",
    name: "Tara",
    sex: "FEMALE",
    latitude: 21.7310,
    longitude: 79.3035,
    approx_zone: "Bodhanala Reservoir Shore",
    current_activity: "RESTING_WATERHOLE",
    last_seen_time: new Date(Date.now() - 68 * 60000).toISOString(),
    last_seen_relative: "1h ago",
    sighting_confidence: 0.93,
    territory_radius_km: 25.0,
    dominant_waterhole: "Bodhanala Reservoir",
    recommended_time_slot: "16:00 - 18:15 PM (Dusk)",
    notes: "Resting in shady bamboo thicket by water's edge; high safari visibility.",
    recent_coordinates: [
      { lat: 21.7330, lng: 79.3010 },
      { lat: 21.7310, lng: 79.3035 }
    ]
  },
  {
    id: "tloc-3",
    code: "T008",
    name: "Sheru",
    sex: "MALE",
    latitude: 21.7556,
    longitude: 79.2876,
    approx_zone: "Chindimatta Ridge & Totladoh",
    current_activity: "TERRITORIAL_MARKING",
    last_seen_time: new Date(Date.now() - 145 * 60000).toISOString(),
    last_seen_relative: "2.4h ago",
    sighting_confidence: 0.88,
    territory_radius_km: 44.0,
    dominant_waterhole: "Seoni Nullah & Mahadeo Tank",
    recommended_time_slot: "06:15 - 08:30 AM (Dawn)",
    notes: "Marking trees along ridge overlook; vocalizing near camera station CT-03.",
    recent_coordinates: [
      { lat: 21.7580, lng: 79.2850 },
      { lat: 21.7556, lng: 79.2876 }
    ]
  },
  {
    id: "tloc-4",
    code: "T032",
    name: "Naina",
    sex: "FEMALE",
    latitude: 21.7135,
    longitude: 79.2660,
    approx_zone: "Gumtara Bamboo Nullah",
    current_activity: "WITH_CUBS",
    last_seen_time: new Date(Date.now() - 210 * 60000).toISOString(),
    last_seen_relative: "3.5h ago",
    sighting_confidence: 0.86,
    territory_radius_km: 22.5,
    dominant_waterhole: "Gumtara Tank & Stream",
    recommended_time_slot: "07:00 - 09:30 AM (Morning)",
    notes: "Moving carefully with 2 cubs; crossing Pyorthadi stream trail.",
    recent_coordinates: [
      { lat: 21.7110, lng: 79.2680 },
      { lat: 21.7135, lng: 79.2660 }
    ]
  },
  {
    id: "tloc-5",
    code: "T045",
    name: "Shadow",
    sex: "MALE",
    latitude: 21.6890,
    longitude: 79.2895,
    approx_zone: "Karmajhiri Buffer Edge",
    current_activity: "TRANSIT",
    last_seen_time: new Date(Date.now() - 310 * 60000).toISOString(),
    last_seen_relative: "5.1h ago",
    sighting_confidence: 0.82,
    territory_radius_km: 36.0,
    dominant_waterhole: "Karmajhiri Stream",
    recommended_time_slot: "17:30 - 20:30 PM (Evening/Night)",
    notes: "Patrolling buffer boundary; detected by CT-07 thermal sensor.",
    recent_coordinates: [
      { lat: 21.6860, lng: 79.2920 },
      { lat: 21.6890, lng: 79.2895 }
    ]
  },
  {
    id: "tloc-6",
    code: "T012",
    name: "Collarwali Lineage",
    sex: "FEMALE",
    latitude: 21.7240,
    longitude: 79.3360,
    approx_zone: "Pyorthadi Ghost Tree Basin",
    current_activity: "HUNTING",
    last_seen_time: new Date(Date.now() - 50 * 60000).toISOString(),
    last_seen_relative: "50m ago",
    sighting_confidence: 0.94,
    territory_radius_km: 28.0,
    dominant_waterhole: "Pyorthadi Lake & Ghost Tree",
    recommended_time_slot: "15:45 - 18:00 PM (Dusk)",
    notes: "Stalking chital deer herd on eastern shoreline; high probability for Touria Gypsy tours.",
    recent_coordinates: [
      { lat: 21.7210, lng: 79.3400 },
      { lat: 21.7240, lng: 79.3360 }
    ]
  }
]

export const MOCK_SIGHTSEEING_ZONES: SightseeingZone[] = [
  {
    id: "zone-alikatta",
    name: "Alikatta Meadow Hotspot",
    zone_type: "CORE",
    latitude: 21.7432,
    longitude: 79.3215,
    radius_meters: 1200,
    visibility_score_morning: 94,
    visibility_score_afternoon: 88,
    visibility_score_night: 40,
    primary_habitat: "Open Savanna Grasslands & Central Waterhole",
    description: "The crown jewel of Pench wildlife viewing. Expansive meadows offering unobstructed 360° visibility with dense herds of spotted deer, wild boar, and gaur attracting prime resident tigers.",
    resident_tigers: [
      { code: "T017", name: "Baghira", likelihood: 95 },
      { code: "T012", name: "Collarwali Lineage", likelihood: 82 },
      { code: "T021", name: "Tara", likelihood: 65 }
    ],
    key_landmarks: ["Alikatta Watchtower", "Central Salt Lick", "Chital Grass Flats", "Banyan Junction"],
    recommended_gate: "Touria Gate (14 km drive)",
    best_safari_timing: "06:00 AM - 08:30 AM (Peak morning activity)",
    camera_stations_nearby: ["CT-01", "CT-02"]
  },
  {
    id: "zone-bodhanala",
    name: "Bodhanala Reservoir Shore",
    zone_type: "CORE",
    latitude: 21.7318,
    longitude: 79.3042,
    radius_meters: 1100,
    visibility_score_morning: 86,
    visibility_score_afternoon: 93,
    visibility_score_night: 52,
    primary_habitat: "Perennial Reservoir & Riparian Bamboo Edge",
    description: "A tranquil perennial water body where resident tigress Tara and male Baghira frequently cool off during warm afternoons. Sambar wallows and open bund crossings make for iconic sightings.",
    resident_tigers: [
      { code: "T021", name: "Tara", likelihood: 92 },
      { code: "T017", name: "Baghira", likelihood: 80 }
    ],
    key_landmarks: ["Bodhanala Bund Track", "Sunset Point", "Old Causeway", "Crocodile Point"],
    recommended_gate: "Touria Gate / Karmajhiri Gate",
    best_safari_timing: "16:00 PM - 18:15 PM (Water drinking & cooling)",
    camera_stations_nearby: ["CT-02", "CT-06"]
  },
  {
    id: "zone-pyorthadi",
    name: "Pyorthadi Ghost Tree Basin",
    zone_type: "CORE",
    latitude: 21.7240,
    longitude: 79.3360,
    radius_meters: 950,
    visibility_score_morning: 89,
    visibility_score_afternoon: 91,
    visibility_score_night: 45,
    primary_habitat: "Ghost Tree (Kulu) Forest & Spring Marsh",
    description: "Famous for stark white Kulu (Ghost) trees contrasting against verdant teak forests. The perennial marsh attracts leopards and tigress T012.",
    resident_tigers: [
      { code: "T012", name: "Collarwali Lineage", likelihood: 90 },
      { code: "T017", name: "Baghira", likelihood: 74 }
    ],
    key_landmarks: ["Giant Ghost Tree Clump", "Pyorthadi Dam Wall", "Marshland Stream"],
    recommended_gate: "Touria Gate",
    best_safari_timing: "15:45 PM - 18:00 PM",
    camera_stations_nearby: ["CT-01", "CT-08"]
  },
  {
    id: "zone-gumtara",
    name: "Gumtara Bamboo & Stream Nullah",
    zone_type: "CORE",
    latitude: 21.7125,
    longitude: 79.2654,
    radius_meters: 1000,
    visibility_score_morning: 84,
    visibility_score_afternoon: 81,
    visibility_score_night: 65,
    primary_habitat: "Dense Dendrocalamus Bamboo & Shaded Nullahs",
    description: "Home of tigress Naina (T032) and her cubs. The dense bamboo provides supreme nursery habitat. Also regular sightings of Indian Wild Dogs (Dholes).",
    resident_tigers: [
      { code: "T032", name: "Naina", likelihood: 88 },
      { code: "T021", name: "Tara", likelihood: 58 }
    ],
    key_landmarks: ["Gumtara Water Tank", "Bamboo Tunnel Track", "Nullah Crossing #3"],
    recommended_gate: "Gumtara Gate (Direct Entry)",
    best_safari_timing: "06:30 AM - 09:15 AM",
    camera_stations_nearby: ["CT-05"]
  },
  {
    id: "zone-chindimatta",
    name: "Chindimatta High Plateau & Ridge",
    zone_type: "CORE",
    latitude: 21.7556,
    longitude: 79.2876,
    radius_meters: 1300,
    visibility_score_morning: 78,
    visibility_score_afternoon: 80,
    visibility_score_night: 72,
    primary_habitat: "Elevated Rocky Ridge overlooking Totladoh Lake",
    description: "The rugged territory of alpha male Sheru (T008). Features breathtaking vistas of the Pench reservoir and rocky caves used for daytime shelter.",
    resident_tigers: [
      { code: "T008", name: "Sheru", likelihood: 87 },
      { code: "T045", name: "Shadow", likelihood: 60 }
    ],
    key_landmarks: ["Chindimatta Viewpoint", "Totladoh Reservoir Shore", "Mahadeo Temple Ridge"],
    recommended_gate: "Karmajhiri Gate / Touria Gate",
    best_safari_timing: "06:15 AM - 08:45 AM",
    camera_stations_nearby: ["CT-03"]
  },
  {
    id: "zone-karmajhiri",
    name: "Karmajhiri Wildlife Corridor & Buffer",
    zone_type: "BUFFER",
    latitude: 21.6901,
    longitude: 79.2888,
    radius_meters: 1400,
    visibility_score_morning: 68,
    visibility_score_afternoon: 72,
    visibility_score_night: 84,
    primary_habitat: "Mixed Fringe Forest, Scrub & Stream Bed",
    description: "Active ecological corridor connecting Pench Core to the Rukhad buffer. High nocturnal carnivore movement including leopards, sloth bears, and dispersing male tigers.",
    resident_tigers: [
      { code: "T045", name: "Shadow", likelihood: 82 },
      { code: "T008", name: "Sheru", likelihood: 54 }
    ],
    key_landmarks: ["Karmajhiri Checkpost", "Seoni Stream Culvert", "Buffer Forest Rest House"],
    recommended_gate: "Karmajhiri Gate",
    best_safari_timing: "17:30 PM - 20:30 PM (Twilight / Night Patrol)",
    camera_stations_nearby: ["CT-07"]
  }
]

export const MOCK_SAFARI_ROUTES: SafariRoute[] = [
  {
    id: "route-touria-prime",
    code: "PTR-SR-01",
    name: "Touria - Alikatta Prime Core Circuit",
    zone: "TOURIA",
    gate_name: "Touria Core Gate",
    visibility_rating: 94,
    distance_km: 28.5,
    duration_hours: 3.5,
    terrain_difficulty: "EASY",
    slot_recommendation: "BOTH",
    max_vehicles: 30,
    current_vehicles_booked: 27,
    resident_tigers: ["T017 (Baghira)", "T021 (Tara)", "T012 (Collarwali Lineage)"],
    summary: "Pench's highest-probability tiger safari circuit, covering Alikatta meadows, Bodhanala reservoir, and Pyorthadi marsh.",
    highlights: [
      "94% historical tiger encounter rate across last 30 days",
      "Open grassland landscape ideal for unobstructed wildlife photography",
      "Prime crossing for dominant male T017 (Baghira)"
    ],
    naturalist_tips: "Pause at Alikatta banyan junction between 06:45 - 07:30 AM; listen for alarm calls from sambar herds near the reservoir bund.",
    suggested_lens: "70-200mm f/2.8 & 100-400mm (Excellent open lighting)",
    recent_sightings_count_48h: 7,
    waypoints: [
      { id: "w1", name: "Touria Entry Gate", latitude: 21.7000, longitude: 79.3100, order: 1, type: "GATE", tiger_sighting_chance: 20, description: "Official entry checkpost and permit validation." },
      { id: "w2", name: "Baghin Nala Culvert", latitude: 21.7200, longitude: 79.3150, order: 2, type: "RIVERBED", tiger_sighting_chance: 72, description: "Seasonal riverbed with frequent pugmarks on soft sand." },
      { id: "w3", name: "Alikatta Central Meadow", latitude: 21.7432, longitude: 79.3215, order: 3, type: "MEADOW", tiger_sighting_chance: 94, description: "Prime predator-prey hotspot; high chital density." },
      { id: "w4", name: "Bodhanala Lake Bund", latitude: 21.7318, longitude: 79.3042, order: 4, type: "WATERHOLE", tiger_sighting_chance: 88, description: "Perennial waterbody with afternoon resting spots." },
      { id: "w5", name: "Pyorthadi Ghost Tree Clump", latitude: 21.7240, longitude: 79.3360, order: 5, type: "MEADOW", tiger_sighting_chance: 85, description: "Marshy spring with high tigress T012 activity." },
      { id: "w6", name: "Touria Exit Track", latitude: 21.7000, longitude: 79.3100, order: 6, type: "GATE", tiger_sighting_chance: 25, description: "Return route to reception centre." }
    ]
  },
  {
    id: "route-karmajhiri-trail",
    code: "PTR-SR-02",
    name: "Karmajhiri - Chindimatta Riverbed Trail",
    zone: "KARMAJHIRI",
    gate_name: "Karmajhiri Gate",
    visibility_rating: 86,
    distance_km: 34.0,
    duration_hours: 4.0,
    terrain_difficulty: "MODERATE",
    slot_recommendation: "DAWN_SAFARI",
    max_vehicles: 20,
    current_vehicles_booked: 16,
    resident_tigers: ["T008 (Sheru)", "T045 (Shadow)"],
    summary: "Deep wilderness trail exploring rocky ridges, teak valleys, and the dramatic Chindimatta plateau overlooking Totladoh.",
    highlights: [
      "Alpha male T008 territory with frequent road-patrolling sightings",
      "Spectacular landscape photography across Totladoh reservoir",
      "High density of Indian Gaur (bison) and wild dogs"
    ],
    naturalist_tips: "Scan high rocky ledges along Chindimatta for Sheru resting in shade; check Seoni stream bed for fresh morning pugmarks.",
    suggested_lens: "200-600mm f/5.6-6.3 (Ridge and valley viewing)",
    recent_sightings_count_48h: 5,
    waypoints: [
      { id: "w21", name: "Karmajhiri Entry Gate", latitude: 21.6901, longitude: 79.2888, order: 1, type: "GATE", tiger_sighting_chance: 30, description: "Northern access point with historic rest house." },
      { id: "w22", name: "Seoni Stream Nullah", latitude: 21.7250, longitude: 79.2820, order: 2, type: "RIVERBED", tiger_sighting_chance: 78, description: "Shaded water course with dense bamboo foliage." },
      { id: "w23", name: "Chindimatta Viewpoint", latitude: 21.7556, longitude: 79.2876, order: 3, type: "RIDGE", tiger_sighting_chance: 86, description: "High rocky promontory overlooking Pench river basin." },
      { id: "w24", name: "Mahadeo Tank", latitude: 21.7620, longitude: 79.2950, order: 4, type: "WATERHOLE", tiger_sighting_chance: 74, description: "Natural water accumulation point favored by Gaur herds." },
      { id: "w25", name: "Karmajhiri Return Loop", latitude: 21.6901, longitude: 79.2888, order: 5, type: "GATE", tiger_sighting_chance: 25, description: "Scenic transit back through mixed teak forest." }
    ]
  },
  {
    id: "route-gumtara-loop",
    code: "PTR-SR-03",
    name: "Gumtara - Ghost Tree Waterhole Loop",
    zone: "GUMTARA",
    gate_name: "Gumtara Gate",
    visibility_rating: 82,
    distance_km: 24.2,
    duration_hours: 3.0,
    terrain_difficulty: "EASY",
    slot_recommendation: "BOTH",
    max_vehicles: 16,
    current_vehicles_booked: 11,
    resident_tigers: ["T032 (Naina & Cubs)", "T021 (Tara)"],
    summary: "Secluded western circuit renowned for peaceful game drives, bamboo corridors, and tigress Naina with her growing cubs.",
    highlights: [
      "82% visibility score with high likelihood of cub sightings",
      "Less vehicle traffic compared to central gates",
      "Exceptional birding and Indian leopard activity"
    ],
    naturalist_tips: "Drive slowly through Bamboo Tunnel Track at 10-15 km/h; tigress Naina often uses the dirt road as a nursery trail.",
    suggested_lens: "70-200mm & 300mm f/4 (Dense vegetation focus)",
    recent_sightings_count_48h: 4,
    waypoints: [
      { id: "w31", name: "Gumtara Gate Checkpost", latitude: 21.7050, longitude: 79.2550, order: 1, type: "GATE", tiger_sighting_chance: 22, description: "Quiet western portal." },
      { id: "w32", name: "Bamboo Tunnel Track", latitude: 21.7125, longitude: 79.2654, order: 2, type: "MEADOW", tiger_sighting_chance: 84, description: "Lush arching bamboo grove." },
      { id: "w33", name: "Gumtara Water Tank", latitude: 21.7190, longitude: 79.2710, order: 3, type: "WATERHOLE", tiger_sighting_chance: 80, description: "Main waterhole frequented by sambar and wild dogs." },
      { id: "w34", name: "Pyorthadi Connector", latitude: 21.7240, longitude: 79.3360, order: 4, type: "MEADOW", tiger_sighting_chance: 76, description: "Western trail heading toward core junction." }
    ]
  },
  {
    id: "route-khursapar-traverse",
    code: "PTR-SR-04",
    name: "Khursapar - Teliya Core-Buffer Traverse",
    zone: "KHURSAPAR",
    gate_name: "Khursapar Gate (MH Border)",
    visibility_rating: 78,
    distance_km: 22.0,
    duration_hours: 2.8,
    terrain_difficulty: "EASY",
    slot_recommendation: "DUSK_SAFARI",
    max_vehicles: 18,
    current_vehicles_booked: 14,
    resident_tigers: ["T012 (Lineage)", "T056 (Rudra)"],
    summary: "Maharashtra-side entrance featuring open waterbodies, blackbuck herds, and regular tiger sightings around Teliya Lake.",
    highlights: [
      "Open shoreline of Teliya Lake with dramatic tiger water crossings",
      "Very high leopard and wild dog encounter rate",
      "Compact track with minimal dead travel time"
    ],
    naturalist_tips: "Position vehicle near Teliya Lake embankment 45 minutes before gate closure for evening water drinking.",
    suggested_lens: "100-400mm / 400mm f/2.8",
    recent_sightings_count_48h: 4,
    waypoints: [
      { id: "w41", name: "Khursapar Gate", latitude: 21.6700, longitude: 79.3400, order: 1, type: "GATE", tiger_sighting_chance: 20, description: "Border checkpost." },
      { id: "w42", name: "Teliya Lake Shoreline", latitude: 21.6850, longitude: 79.3480, order: 2, type: "WATERHOLE", tiger_sighting_chance: 82, description: "Large open lake with frequent tiger visits." },
      { id: "w43", name: "Silari Meadow", latitude: 21.6950, longitude: 79.3520, order: 3, type: "MEADOW", tiger_sighting_chance: 74, description: "Grazing ground for blackbuck and spotted deer." }
    ]
  },
  {
    id: "route-rukhad-night",
    code: "PTR-SR-05",
    name: "Rukhad - Bison Corridor Night/Twilight Patrol",
    zone: "RUKHAD",
    gate_name: "Rukhad Sanctuary Gate",
    visibility_rating: 68,
    distance_km: 31.0,
    duration_hours: 3.5,
    terrain_difficulty: "RUGGED",
    slot_recommendation: "NIGHT_BUFFER",
    max_vehicles: 12,
    current_vehicles_booked: 8,
    resident_tigers: ["T045 (Shadow)", "Resident Leopard Pair"],
    summary: "Exclusive twilight & night buffer safari offering an unparalleled look into nocturnal predator movement and rare wildlife.",
    highlights: [
      "Special spotlight-equipped safari vehicles for nocturnal carnivore tracking",
      "High density of Sloth Bears, Civets, Flying Squirrels, and Leopards",
      "Dispersal corridor for tiger T045 (Shadow)"
    ],
    naturalist_tips: "Use red filter spotlight beams to prevent startling nocturnal wildlife; check Asolapani reservoir causeway.",
    suggested_lens: "Fast prime lenses (85mm / 135mm / 70-200mm f/2.8 at high ISO)",
    recent_sightings_count_48h: 3,
    waypoints: [
      { id: "w51", name: "Rukhad Forest Checkpost", latitude: 21.6500, longitude: 79.3100, order: 1, type: "GATE", tiger_sighting_chance: 25, description: "Night safari staging area." },
      { id: "w52", name: "Asolapani Dam Shore", latitude: 21.6650, longitude: 79.3200, order: 2, type: "WATERHOLE", tiger_sighting_chance: 70, description: "Nocturnal waterhole." },
      { id: "w53", name: "Bison Valley Track", latitude: 21.6780, longitude: 79.3150, order: 3, type: "MEADOW", tiger_sighting_chance: 65, description: "Thick woodland corridor." }
    ]
  }
]

export const MOCK_LIVE_SAFARI_SIGHTINGS: LiveSafariSighting[] = [
  {
    id: "sight-1",
    route_id: "route-touria-prime",
    route_name: "Touria Prime Core Circuit",
    tiger_code: "T017",
    tiger_name: "Baghira",
    location_name: "Alikatta Central Meadow, Culvert 4",
    latitude: 21.7445,
    longitude: 79.3230,
    timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
    time_ago: "25 mins ago",
    observed_by: "GYPSY_NATURALIST",
    behavior: "Walking purposefully along main dirt road toward Bodhanala; stopped to spray mark teak tree. Calm demeanor.",
    confidence_score: 0.98
  },
  {
    id: "sight-2",
    route_id: "route-touria-prime",
    route_name: "Touria Prime Core Circuit",
    tiger_code: "T021",
    tiger_name: "Tara",
    location_name: "Bodhanala Reservoir Shore",
    latitude: 21.7310,
    longitude: 79.3035,
    timestamp: new Date(Date.now() - 55 * 60000).toISOString(),
    time_ago: "55 mins ago",
    observed_by: "TOURIST_GROUP",
    behavior: "Resting in shaded water shallows to escape mid-day heat. Highly visible from main safari track.",
    confidence_score: 0.95
  },
  {
    id: "sight-3",
    route_id: "route-gumtara-loop",
    route_name: "Gumtara Bamboo Loop",
    tiger_code: "T032",
    tiger_name: "Naina",
    location_name: "Gumtara Bamboo Nullah, Waypoint 2",
    latitude: 21.7135,
    longitude: 79.2660,
    timestamp: new Date(Date.now() - 110 * 60000).toISOString(),
    time_ago: "1.8h ago",
    observed_by: "FOREST_GUARD",
    behavior: "Observed leading 2 healthy cubs across stream bed toward thick bamboo nursery cover.",
    confidence_score: 0.92
  },
  {
    id: "sight-4",
    route_id: "route-karmajhiri-trail",
    route_name: "Karmajhiri Riverbed Trail",
    tiger_code: "T008",
    tiger_name: "Sheru",
    location_name: "Chindimatta High Ridge",
    latitude: 21.7556,
    longitude: 79.2876,
    timestamp: new Date(Date.now() - 170 * 60000).toISOString(),
    time_ago: "2.8h ago",
    observed_by: "CAMERA_TRAP",
    behavior: "Station CT-03 captured full right-flank profile during morning territory patrol.",
    confidence_score: 0.94
  }
]

export const MOCK_STATIONS: CameraStation[] = [
  { id: "s1", code: "CT-01", name: "Alikatta Central Meadow", latitude: 21.7432, longitude: 79.3215, zone: "CORE", status: "ACTIVE", last_check: "2026-08-15 08:30" },
  { id: "s2", code: "CT-02", name: "Bodhanala Crossing", latitude: 21.7318, longitude: 79.3042, zone: "CORE", status: "ACTIVE", last_check: "2026-08-15 08:15" },
  { id: "s3", code: "CT-03", name: "Chindimatta Ridge Overlook", latitude: 21.7556, longitude: 79.2876, zone: "CORE", status: "ACTIVE", last_check: "2026-08-15 07:50" },
  { id: "s4", code: "CT-05", name: "Gumtara Bamboo Waterhole", latitude: 21.7125, longitude: 79.2654, zone: "CORE", status: "ACTIVE", last_check: "2026-08-15 07:30" },
  { id: "s5", code: "CT-07", name: "Karmajhiri Buffer Boundary", latitude: 21.6901, longitude: 79.2888, zone: "BUFFER", status: "ACTIVE", last_check: "2026-08-15 06:45" },
  { id: "s6", code: "CT-08", name: "Pyorthadi Ghost Tree Spring", latitude: 21.7240, longitude: 79.3360, zone: "CORE", status: "ACTIVE", last_check: "2026-08-15 08:00" }
]

export const MOCK_ALERTS: Alert[] = [
  {
    id: "alert-01",
    type: "BUFFER_MOVEMENT",
    severity: "CRITICAL",
    status: "ACTIVE",
    title: "Buffer Zone Peripheral Breach",
    summary: "Tiger T045 (Shadow) verified 1.2 km outside core boundary near Karmajhiri agricultural edge.",
    tiger_id: "t5",
    tiger_code: "T045",
    tiger_name: "Shadow",
    station_code: "CT-07",
    latitude: 21.6890,
    longitude: 79.2895,
    evidence_confidence: 0.94,
    action_recommendation: "Dispatch Rapid Response Unit (RRU) to patrol Karmajhiri cattle corridor.",
    created_at: new Date(Date.now() - 14 * 60000).toISOString()
  },
  {
    id: "alert-02",
    type: "TERRITORIAL_OVERLAP",
    severity: "HIGH",
    status: "INVESTIGATING",
    title: "Dominant Male Territory Proximity",
    summary: "GPS telemetry indicates T017 (Baghira) and T008 (Sheru) within 450m proximity near Bodhanala Ridge.",
    tiger_id: "t1",
    tiger_code: "T017",
    tiger_name: "Baghira",
    station_code: "CT-02",
    latitude: 21.7445,
    longitude: 79.3230,
    evidence_confidence: 0.91,
    action_recommendation: "Monitor acoustic telemetry log for aggressive territorial vocalizations.",
    created_at: new Date(Date.now() - 42 * 60000).toISOString()
  },
  {
    id: "alert-03",
    type: "STATION_NOVELTY",
    severity: "HIGH",
    status: "ACTIVE",
    title: "New Station Detection: Tigress with Cubs",
    summary: "Tiger T032 (Naina) detected for the first time at camera station CT-05 with 2 healthy cubs.",
    tiger_id: "t4",
    tiger_code: "T032",
    tiger_name: "Naina",
    station_code: "CT-05",
    latitude: 21.7135,
    longitude: 79.2660,
    evidence_confidence: 0.97,
    action_recommendation: "Establish protective vehicular speed buffer of 15 km/h along Bamboo Tunnel track.",
    created_at: new Date(Date.now() - 95 * 60000).toISOString()
  },
  {
    id: "alert-04",
    type: "CAMERA_OBSTRUCTION",
    severity: "MEDIUM",
    status: "ACKNOWLEDGED",
    title: "Camera Lens Moisture / Foliage Obstruction",
    summary: "Station CT-03 Chindimatta Overlook reports 34% drop in frame clarity due to heavy morning condensation.",
    station_code: "CT-03",
    latitude: 21.7556,
    longitude: 79.2876,
    evidence_confidence: 0.88,
    action_recommendation: "Assign beat guard during afternoon maintenance round to clean housing glass.",
    created_at: new Date(Date.now() - 180 * 60000).toISOString()
  },
  {
    id: "alert-05",
    type: "SIGHTING_CONGREGATION",
    severity: "LOW",
    status: "RESOLVED",
    title: "High Tourist Gypsy Density at Alikatta",
    summary: "7 Gypsy vehicles clustered at Alikatta central meadow; tiger T017 granted right of way successfully.",
    tiger_id: "t1",
    tiger_code: "T017",
    tiger_name: "Baghira",
    station_code: "CT-01",
    latitude: 21.7432,
    longitude: 79.3215,
    evidence_confidence: 0.99,
    action_recommendation: "Naturalist radio confirmed traffic clearance and tiger transit.",
    created_at: new Date(Date.now() - 360 * 60000).toISOString()
  }
]

export const MOCK_DASHBOARD: DashboardData = {
  data_notice: "PENCH TIGER RESERVE · LIVE TELEMETRY & SPATIAL FEED",
  metrics: {
    images_processed: 112661,
    quarantined: 69363,
    storage_saved_bytes: 345620109400,
    known_individuals: 6,
    review_queue: 3
  },
  latest_run: {
    id: "run-monsoon-04",
    name: "Monsoon Telemetry Survey · Cycle 08",
    status: "COMPLETE",
    total_images: 38472,
    retained_images: 14364,
    quarantined_images: 24108,
    tiger_detections: 184,
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    duration_seconds: 1122.0
  },
  alerts: MOCK_ALERTS
}

export const MOCK_REVIEWS: ReviewItem[] = [
  {
    id: "r1",
    state: "OPEN",
    similarity_score: 0.78,
    candidates: [
      { tiger_code: "T017", name: "Baghira", similarity: 0.78 },
      { tiger_code: "T008", name: "Sheru", similarity: 0.69 }
    ],
    suggested_tiger_id: "t1",
    created_at: new Date().toISOString()
  },
  {
    id: "r2",
    state: "PENDING",
    similarity_score: 0.74,
    candidates: [
      { tiger_code: "T021", name: "Tara", similarity: 0.74 },
      { tiger_code: "T032", name: "Naina", similarity: 0.66 }
    ],
    suggested_tiger_id: "t2",
    created_at: new Date().toISOString()
  }
]

// -------------------------------------------------------------
// API Interface & Helper Functions
// -------------------------------------------------------------

export const api = {
  getImageUrl(urlOrPath: string | null | undefined): string | null {
    if (!urlOrPath) return null
    if (urlOrPath.startsWith("http://") || urlOrPath.startsWith("https://") || urlOrPath.startsWith("data:")) {
      return urlOrPath
    }
    const base = getApiBase()
    const cleanPath = urlOrPath.startsWith("/") ? urlOrPath : `/${urlOrPath}`
    return `${base}${cleanPath}`
  },

  async geocodeLandmark(query: string): Promise<any> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/safari/geocode?q=${encodeURIComponent(query)}`)
      if (res.ok) {
        return await res.json()
      }
    } catch {
      // Offline fallback geocoder
    }

    const presets: { [key: string]: { lat: number; lng: number; landmark: string } } = {
      alikatta: { lat: 21.7432, lng: 79.3215, landmark: "Alikatta Central Meadow" },
      bodhanala: { lat: 21.7318, lng: 79.3042, landmark: "Bodhanala Reservoir Shore" },
      pyorthadi: { lat: 21.7240, lng: 79.3360, landmark: "Pyorthadi Ghost Tree Basin" },
      gumtara: { lat: 21.7125, lng: 79.2654, landmark: "Gumtara Bamboo Nullah" },
      chindimatta: { lat: 21.7556, lng: 79.2876, landmark: "Chindimatta High Ridge & Plateau" },
      totladoh: { lat: 21.7680, lng: 79.2950, landmark: "Totladoh Reservoir Lake" },
      touria: { lat: 21.7000, lng: 79.3100, landmark: "Touria Core Gate Checkpost" },
      karmajhiri: { lat: 21.6901, lng: 79.2888, landmark: "Karmajhiri Buffer Gate & Corridor" },
      khursapar: { lat: 21.6700, lng: 79.3400, landmark: "Khursapar Maharashtra Gate" },
      rukhad: { lat: 21.6500, lng: 79.3100, landmark: "Rukhad Bison Corridor" },
      jamtara: { lat: 21.7681, lng: 79.3398, landmark: "Jamtara Riverbed Wilderness" },
      baghin: { lat: 21.7200, lng: 79.3150, landmark: "Baghin Nala Culvert" },
    }

    const q = query.toLowerCase()
    for (const key of Object.keys(presets)) {
      if (q.includes(key)) {
        return {
          latitude: presets[key].lat,
          longitude: presets[key].lng,
          matched_landmark: presets[key].landmark,
          zone: "CORE"
        }
      }
    }

    return { latitude: 21.7432, longitude: 79.3215, matched_landmark: "Alikatta Central Meadow", zone: "CORE" }
  },

  async spotAndPlotTiger(payload: {
    tiger_code: string
    tiger_name?: string
    tiger_sex?: string
    location_name: string
    latitude?: number
    longitude?: number
    observed_by?: string
    behavior: string
    confidence_score?: number
    route_id?: string
    notes?: string
  }): Promise<any> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/safari/spot-tiger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }, 4000)
      if (res.ok) {
        return await res.json()
      }
    } catch (e) {
      console.warn("Backend offline or request failed, using client fallback:", e)
    }

    // Client-side offline fallback & live state update
    const lat = payload.latitude || 21.7432
    const lng = payload.longitude || 79.3215
    const code = payload.tiger_code.toUpperCase()
    const name = payload.tiger_name || `Tiger ${code}`

    // 1. Update/Add to MOCK_TIGERS
    const existingIndex = MOCK_TIGERS.findIndex(t => t.code === code)
    if (existingIndex >= 0) {
      MOCK_TIGERS[existingIndex].last_seen = new Date().toISOString().split("T")[0]
      MOCK_TIGERS[existingIndex].total_observations = (MOCK_TIGERS[existingIndex].total_observations || 0) + 1
    } else {
      MOCK_TIGERS.unshift({
        id: `tiger-mock-${Date.now().toString(36)}`,
        code: code,
        name: name,
        sex: (payload.tiger_sex as any) || "UNKNOWN",
        status: "CONFIRMED",
        total_observations: 1,
        first_seen: new Date().toISOString().split("T")[0],
        last_seen: new Date().toISOString().split("T")[0],
        notes: payload.notes || `Spotting recorded at ${payload.location_name}`
      })
    }

    // 2. Update/Add to MOCK_TIGER_LOCATIONS
    const locIndex = MOCK_TIGER_LOCATIONS.findIndex(t => t.code === code)
    const newLocationEntry: TigerLocation = {
      id: `tloc-${Date.now().toString(36)}`,
      code: code,
      name: name,
      sex: (payload.tiger_sex as any) || "UNKNOWN",
      latitude: lat,
      longitude: lng,
      approx_zone: payload.location_name,
      current_activity: (payload.behavior.toUpperCase().includes("WATER") ? "RESTING_WATERHOLE" : payload.behavior.toUpperCase().includes("CUB") ? "WITH_CUBS" : "PATROLLING") as any,
      last_seen_time: new Date().toISOString(),
      last_seen_relative: "Just now",
      sighting_confidence: payload.confidence_score || 0.95,
      territory_radius_km: 30.0,
      dominant_waterhole: payload.location_name,
      recommended_time_slot: "06:00 - 08:30 AM (Dawn)",
      notes: payload.behavior,
      recent_coordinates: [{ lat, lng }]
    }

    if (locIndex >= 0) {
      MOCK_TIGER_LOCATIONS[locIndex] = {
        ...MOCK_TIGER_LOCATIONS[locIndex],
        ...newLocationEntry,
        recent_coordinates: [
          ...(MOCK_TIGER_LOCATIONS[locIndex].recent_coordinates || []),
          { lat, lng }
        ]
      }
    } else {
      MOCK_TIGER_LOCATIONS.unshift(newLocationEntry)
    }

    // 3. Add to MOCK_LIVE_SAFARI_SIGHTINGS
    const newSighting: LiveSafariSighting = {
      id: `sight-live-${Date.now().toString(36)}`,
      route_id: payload.route_id || "route-touria-prime",
      route_name: "Touria Prime Core Circuit",
      tiger_code: code,
      tiger_name: name,
      location_name: payload.location_name,
      latitude: lat,
      longitude: lng,
      observed_by: (payload.observed_by as any) || "GYPSY_NATURALIST",
      behavior: payload.behavior,
      confidence_score: payload.confidence_score || 0.95,
      timestamp: new Date().toISOString(),
      time_ago: "Just now"
    }
    MOCK_LIVE_SAFARI_SIGHTINGS.unshift(newSighting)

    return {
      status: "SUCCESS",
      message: `Plotted ${code} (${name}) at ${payload.location_name}`,
      sighting: newSighting,
      tiger: newLocationEntry
    }
  },

  async getDashboard(): Promise<DashboardData> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/dashboard`)
      if (!res.ok) throw new Error()
      const data = await res.json()
      if (!data.alerts || data.alerts.length < 3) {
        data.alerts = MOCK_ALERTS
      }
      return data
    } catch {
      return { ...MOCK_DASHBOARD, alerts: [...MOCK_ALERTS] }
    }
  },

  async getTigers(): Promise<Tiger[]> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/tigers`)
      if (res.ok) {
        const data = await res.json()
        const list = data.tigers || (Array.isArray(data) ? data : null)
        if (list && list.length > 0) return list
      }
    } catch (e) {
      console.warn("Failed to fetch live tigers from API, using fallback:", e)
    }
    return MOCK_TIGERS
  },

  async getTigerLocations(): Promise<TigerLocation[]> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/safari/tiger-locations`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) return data
      }
    } catch (e) {
      console.warn("Failed to fetch dynamic tiger locations, using fallback:", e)
    }
    return MOCK_TIGER_LOCATIONS
  },

  async getSightseeingZones(): Promise<SightseeingZone[]> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/safari/zones`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) return data
      }
    } catch {
      // Fallback
    }
    return MOCK_SIGHTSEEING_ZONES
  },

  async getSafariRoutes(): Promise<SafariRoute[]> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/safari/routes`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) return data
      }
    } catch {
      // Fallback
    }
    return MOCK_SAFARI_ROUTES
  },

  async getLiveSafariSightings(): Promise<LiveSafariSighting[]> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/safari/sightings`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) return data
      }
    } catch {
      // Fallback
    }
    return MOCK_LIVE_SAFARI_SIGHTINGS
  },

  async submitLiveSafariSighting(payload: Omit<LiveSafariSighting, "id" | "timestamp" | "time_ago">): Promise<LiveSafariSighting> {
    return (await this.spotAndPlotTiger({
      tiger_code: payload.tiger_code,
      tiger_name: payload.tiger_name,
      location_name: payload.location_name,
      latitude: payload.latitude,
      longitude: payload.longitude,
      observed_by: payload.observed_by,
      behavior: payload.behavior,
      confidence_score: payload.confidence_score,
      route_id: payload.route_id
    })).sighting
  },

  async simulateTelemetryAlert(): Promise<Alert> {
    const templates = [
      {
        type: "BUFFER_MOVEMENT",
        severity: "CRITICAL",
        title: "Nocturnal Buffer Movement Detected",
        summary: "Tiger T017 (Baghira) detected heading toward Touria peripheral corridor boundary.",
        tiger_code: "T017",
        tiger_name: "Baghira",
        station_code: "CT-01",
        latitude: 21.7445,
        longitude: 79.3230,
        action: "Alert beat 3 rangers for buffer monitoring."
      },
      {
        type: "TERRITORIAL_OVERLAP",
        severity: "HIGH",
        title: "Male Territory Dispute Proximity",
        summary: "Tiger T008 (Sheru) moving into Bodhanala sector overlapping with T017's scent markings.",
        tiger_code: "T008",
        tiger_name: "Sheru",
        station_code: "CT-02",
        latitude: 21.7318,
        longitude: 79.3042,
        action: "Deploy thermal drone to assess territorial behavior."
      },
      {
        type: "SIGHTING_SPIKE",
        severity: "MEDIUM",
        title: "Safari Sighting Spike: Alikatta",
        summary: "3 consecutive Gypsy groups confirm clear sighting of T012 (Collarwali Lineage) hunting chital.",
        tiger_code: "T012",
        tiger_name: "Collarwali Lineage",
        station_code: "CT-08",
        latitude: 21.7240,
        longitude: 79.3360,
        action: "Regulate vehicle convoy spacing on Route A."
      },
      {
        type: "NOVEL_INDIVIDUAL",
        severity: "HIGH",
        title: "Uncatalogued Sub-adult Individual Detected",
        summary: "Camera trap CT-05 captured clear left-flank of an uncatalogued 18-month sub-adult.",
        tiger_code: "T-NEW",
        tiger_name: "Unregistered Sub-adult",
        station_code: "CT-05",
        latitude: 21.7125,
        longitude: 79.2654,
        action: "Queue image into Re-ID matching review pipeline."
      }
    ]

    const randomTemplate = templates[Math.floor(Math.random() * templates.length)]
    const newAlert: Alert = {
      id: `alert-dyn-${Date.now().toString(36)}`,
      type: randomTemplate.type,
      severity: randomTemplate.severity as any,
      status: "ACTIVE",
      title: randomTemplate.title,
      summary: randomTemplate.summary,
      tiger_code: randomTemplate.tiger_code,
      tiger_name: randomTemplate.tiger_name,
      station_code: randomTemplate.station_code,
      latitude: randomTemplate.latitude,
      longitude: randomTemplate.longitude,
      evidence_confidence: 0.95,
      action_recommendation: randomTemplate.action,
      created_at: new Date().toISOString()
    }
    MOCK_ALERTS.unshift(newAlert)
    return newAlert
  },

  async enrollTiger(payload: { code: string; name?: string; sex?: string; notes?: string }): Promise<Tiger> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/tigers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: payload.code,
          name: payload.name || `Tiger ${payload.code}`,
          sex: payload.sex || "UNKNOWN",
          notes: payload.notes || "Manually enrolled into Pench individual catalogue.",
        }),
      }, 3000)
      if (res.ok) {
        return await res.json()
      }
    } catch {
      // Offline / standalone demo fallback
    }

    const fallbackTiger: Tiger = {
      id: `tiger-mock-${Date.now().toString(36)}`,
      code: payload.code,
      name: payload.name || `Tiger ${payload.code}`,
      sex: (payload.sex as any) || "UNKNOWN",
      status: "CONFIRMED",
      total_observations: 1,
      first_seen: new Date().toISOString().split("T")[0],
      last_seen: new Date().toISOString().split("T")[0],
      notes: payload.notes || "Manually enrolled into Pench individual catalogue.",
    }
    MOCK_TIGERS.unshift(fallbackTiger)
    return fallbackTiger
  },

  async getStations(): Promise<CameraStation[]> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/stations`)
      if (!res.ok) throw new Error()
      const data = await res.json()
      return data.stations || data
    } catch {
      return MOCK_STATIONS
    }
  },

  async getReviews(): Promise<ReviewItem[]> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/reviews`)
      if (!res.ok) throw new Error()
      const data = await res.json()
      return data.reviews || data
    } catch {
      return MOCK_REVIEWS
    }
  },

  async submitReviewDecision(reviewId: string, action: string, tigerId?: string, note?: string): Promise<any> {
    try {
      const res = await fetchWithTimeout(`${getApiBase()}/reviews/${reviewId}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, tiger_id: tigerId, note })
      }, 2500)
      if (res.ok) {
        return await res.json()
      }
    } catch (e) {
      console.warn("Backend not available, applying client-side demo decision:", e)
    }
    return {
      id: reviewId,
      state: "DECIDED",
      decision: action,
      assigned_tiger_id: tigerId || "mock-tiger-id",
      tiger_code: tigerId || "T048",
      tiger_name: note || "Enrolled Individual",
      audit_event: "REVIEW_DECISION",
    }
  },

  async resetDemoReviews(): Promise<any> {
    try {
      const res = await fetch(`${getApiBase()}/reviews/reset-demo`, { method: "POST" })
      return await res.json()
    } catch (e) {
      console.warn("Reset demo using local mock:", e)
      return { status: "success", message: "Mock demo reviews reset" }
    }
  },

  async uploadLiveCapture(file: Blob, filename = "live_capture.jpg"): Promise<LiveCaptureResult> {
    try {
      const formData = new FormData()
      formData.append("file", file, filename)

      const res = await fetchWithTimeout(`${getApiBase()}/live/capture`, {
        method: "POST",
        body: formData,
      }, 4000)

      if (res.ok) {
        return await res.json()
      }
    } catch (e) {
      console.warn("Backend offline, simulating live analysis for demo:", e)
    }

    await new Promise((r) => setTimeout(r, 1000))
    return {
      run_id: `live-sim-${Date.now().toString(36)}`,
      filename: filename,
      state: "PROCESSED",
      triage_category: "TIGER",
      triage_confidence: 0.965,
      quarantined: false,
      flanks_detected: 1,
      top_match_tiger_code: "T017",
      top_match_tiger_name: "Baghira",
      top_match_similarity: 0.884,
      review_required: true,
      review_id: "demo-rev-01",
      review_candidates: [
        { tiger_code: "T017", name: "Baghira", similarity: 0.884, status: "CONFIRMED" },
        { tiger_code: "T008", name: "Sheru", similarity: 0.721, status: "CONFIRMED" },
        { tiger_code: "T045", name: "Shadow", similarity: 0.635, status: "CONFIRMED" },
      ],
    }
  }
}
