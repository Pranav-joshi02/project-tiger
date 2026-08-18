# Pench Tiger Intelligence System · Architecture & Pipeline Specification

This document details the end-to-end architecture, multi-stage processing pipeline, and operational workflows of **Project Tiger (Pench National Park & Tiger Reserve)**.

---

## 1. System Architecture Overview

```mermaid
flowchart TB
    subgraph S1["Stage 1: Camera Trap & Ingestion"]
        CT["📸 Camera Trap Network<br/>(40+ Stations in Core & Buffer)"] --> UPL["📥 Ingestion Gateway / Live Upload<br/>(/live/capture & /runs)"]
        UPL --> S3RAW[("🪣 MinIO Object Storage<br/>raw-images bucket")]
        UPL --> EXIF["🕒 Metadata & EXIF Extractor<br/>(GPS, Timestamp, Station ID)"]
    end

    subgraph S2["Stage 2: AI Triage & Quarantine Gate"]
        S3RAW --> MD["🤖 MegaDetector / YOLOv8 Triage<br/>(Animal vs Blank vs Vehicle vs Ranger)"]
        MD -->|Blank / Non-Wildlife >60%| QUAR[("🚫 Quarantine Storage<br/>(345+ GB Storage Saved)")]
        MD -->|Wildlife / Tiger Confirmed| QFILTER["🔍 Image Quality & Lighting Assessment<br/>(Blur, Exposure, Occlusion Score)"]
    end

    subgraph S3["Stage 3: Flank Cropping & Re-ID Embeddings"]
        QFILTER --> FLANK["🐯 YOLO Flank Detector & Segmentor<br/>(Left vs Right Flank Segmentation)"]
        FLANK --> CROP[("🪣 MinIO Object Storage<br/>flanks & crops bucket")]
        FLANK --> REID["🧠 Deep Feature Extractor / Stripe Re-ID<br/>(512-dim Vector Embedding Generator)"]
    end

    subgraph S4["Stage 4: Vector Similarity Search (pgvector)"]
        REID --> PGV[("🐘 PostgreSQL 16 + pgvector<br/>(Cosine / L2 Prototype Index)")]
        PGV --> TOPK["📊 Ranked Similarity Matcher<br/>(Top-3 Database Matches Ranked)"]
    end

    subgraph S5["Stage 5: Human-in-the-Loop & Decision Engine (CURRENT STAGE)"]
        TOPK --> EVAL{"Confidence Threshold"}
        EVAL -->|Sim ≥ 92%| AUTO["⚡ Auto-Matched<br/>(Automated Sighting Scribing)"]
        EVAL -->|70% ≤ Sim < 92%| REVQUEUE["🛡️ Human Review Queue<br/>(Side-by-Side Comparison UI)"]
        EVAL -->|Sim < 70% or Novel| NEWIND["✨ Novel Individual Candidate<br/>(Auto-Suggest Next ID: T046+)"]
        
        REVQUEUE -->|Accept Match| CONFIRMED["✅ Confirmed Observation Linked"]
        REVQUEUE -->|Enroll New| ENROLLED["🐯 Brand New Tiger Enrolled"]
        REVQUEUE -->|Reject| REJ["❌ False Positive Dismissed"]
    end

    subgraph S6["Stage 6: Persistence & Spatial Analytics (PostGIS)"]
        AUTO --> DB[("🐘 PostgreSQL / PostGIS Database<br/>tigers, observations, stations, encounters")]
        CONFIRMED --> DB
        ENROLLED --> DB
        DB --> SPATIAL["🗺️ Spatial Engine & Movement Corridors<br/>(Core vs Buffer Zone Transits)"]
        DB --> STATS["📈 Population & Census Analytics"]
    end

    subgraph S7["Stage 7: Interactive Dashboard & Review UI (CURRENT STAGE)"]
        DB <---> API["⚡ FastAPI Async REST Service<br/>(:8000 & /api reverse proxy)"]
        API <---> NGINX["🌐 Nginx Web Proxy (:3000)"]
        NGINX <---> UI["💻 React + Vite + Tailwind Dashboard<br/>- Review Queue Side-by-Side<br/>- Live Camera Capture & Triage<br/>- Tiger Individual Catalogue<br/>- GPS Reserve Territory Map"]
    end

    classDef activeStage fill:#1b4332,stroke:#d4af37,stroke-width:2.5px,color:#fff;
    class S5,S7 activeStage;
```

---

## 2. Multi-Stage Pipeline Breakdown

| Stage | Name | Technology / Component | What Happens Here | Operational Status |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | **Ingestion & Telemetry** | FastAPI, MinIO S3, ExifTool | Camera-trap SD card batches or live edge uploads are received, hashed (SHA-256), and stored in raw object storage with GPS tags and timestamps. | Automated |
| **Stage 2** | **AI Triage & Quarantine** | YOLOv8 / MegaDetector | 60%+ of camera-trap photos are blank (wind movement, leaves) or non-wildlife. The system auto-quarantines these, saving hundreds of gigabytes of disk storage. | Automated |
| **Stage 3** | **Flank Detection & Stripe Re-ID** | PyTorch, OpenCV, ResNet | Isolates the left or right tiger flank, crops the stripe pattern, assesses visual quality, and extracts a 512-dimensional vector embedding. | Automated |
| **Stage 4** | **Vector Search** | PostgreSQL 16 + `pgvector` | Compares the 512-dim embedding against all confirmed tiger prototypes in the reserve using cosine similarity distance. | Automated |
| **Stage 5** | **Human Verification & Enrollment** *(Our Stage)* | FastAPI Review Engine, Postgres Models | Ranks top database candidates. Biologists and rangers visually compare the live capture side-by-side with prototype matches to confirm identity or enroll a new tiger. | **Active & Enhanced** |
| **Stage 6** | **Spatial Telemetry & Sighting History** | PostGIS, GeoJSON | Sighting coordinates are registered into territory maps to track corridor movements (e.g. Alikatta, Bodhanala, Karmajhiri buffer). | Operational |
| **Stage 7** | **Operations Dashboard** *(Our Stage)* | React, Vite, Tailwind CSS, Lucide | Dark-forest aesthetic management interface with review queues, live pipeline simulation, individual profiles, and interactive reserve maps. | **Active & Enhanced** |

---

## 3. Our Focus Area: Stages 5 & 7 (Human Verification & Dashboard)

```mermaid
sequenceDiagram
    autonumber
    actor Ranger as 🧑‍🌾 Reserve Biologist / Ranger
    participant UI as 💻 Review Queue UI (React)
    participant Proxy as 🌐 Nginx Proxy (/api)
    participant API as ⚡ FastAPI Backend
    participant DB as 🐘 PostgreSQL (pgvector)
    participant S3 as 🪣 MinIO Storage

    Note over Ranger, S3: Human-in-the-Loop Sighting Verification
    Ranger->>UI: Opens /review queue
    UI->>Proxy: GET /api/reviews
    Proxy->>API: GET /reviews (filtered for OPEN / PENDING)
    API->>DB: Query pending reviews with ranked candidates
    DB-->>API: Return candidates (e.g. T017 Baghira 84%, Sheru 71%)
    API-->>UI: JSON Payload with query image & candidate photos
    UI-->>Ranger: Renders side-by-side comparison with match progress bar

    alt Decision: Accept Database Match
        Ranger->>UI: Clicks "Accept Match" (e.g. T017 Baghira)
        UI->>Proxy: POST /api/reviews/{id}/decision {action: "ACCEPT_CANDIDATE", tiger_id: "T017"}
        Proxy->>API: Route decision
        API->>DB: Update Review (DECIDED), link Observation with station, update tiger stats
        DB-->>API: Commit transaction
        API-->>UI: HTTP 200 {state: "DECIDED", tiger: "T017 Baghira"}
        UI-->>Ranger: Optimistically advance queue & display success toast
    else Decision: Enroll Brand New Tiger
        Ranger->>UI: Clicks "Enroll as New Tiger" (e.g. Name: "Rudra")
        UI->>Proxy: POST /api/reviews/{id}/decision {action: "ENROLL_NEW", note: "Rudra"}
        Proxy->>API: Route enrollment
        API->>DB: Auto-increment tiger code (T046 -> T047), create Tiger, attach embeddings
        DB-->>API: Commit transaction
        API-->>UI: HTTP 200 {state: "DECIDED", tiger_code: "T047", name: "Rudra"}
        UI-->>Ranger: Display "Enrolled T047" & update Tigers Catalogue
    end
```

---

## 4. Key Highlights of Our Architecture

1. **Zero-Latency In-Memory Client Fallback**:
   - The frontend (`apps/frontend`) is architected with a decoupled API layer (`api.ts`).
   - If deployed statically to Vercel/Netlify for approval without backend hosting, the entire interactive dashboard falls back seamlessly to client-side simulations.

2. **pgvector High-Speed Retrieval**:
   - Tiger stripe biometric embeddings are queried via SQL vector operations (`<->` / cosine metric), resolving candidate matches in milliseconds across thousands of sightings.

3. **Storage-Optimized Quarantine Gate**:
   - Non-wildlife and false-trigger photos are isolated before heavy downstream processing, saving over 60% disk storage.
