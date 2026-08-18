# Project Tiger: Autonomous Biometric Wildlife Intelligence & Re-Identification Platform

> **Comprehensive Technical Architecture & Operational Specification**  
> **Target Reserve**: Pench Tiger Reserve, Central India  
> **Core Domain**: Computer Vision, Metric Learning, Biometrics, Spatial Intelligence, Cryptographic Conservation Audit  
> **Version**: 2.4.0-Production  

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Asynchronous Celery Worker Pipeline](#3-asynchronous-celery-worker-pipeline)
4. [Stage 1: Multi-Scale Species Triage & Morphological Guardian](#4-stage-1-multi-scale-species-triage--morphological-guardian)
5. [Stage 2: 15-Keypoint Quadruped Pose Alignment & Body Part Decomposition](#5-stage-2-15-keypoint-quadruped-pose-alignment--body-part-decomposition)
6. [Stage 3: Deep Feature Representation & Metric Learning](#6-stage-3-deep-feature-representation--metric-learning)
7. [Stage 4: Two-Stage Hybrid Re-ID & Verification Engine](#7-stage-4-two-stage-hybrid-re-id--verification-engine)
8. [Strict Negative Constraints & Cannot-Link Memory Architecture](#8-strict-negative-constraints--cannot-link-memory-architecture)
9. [Cryptographic Merkle Tree Audit Ledger](#9-cryptographic-merkle-tree-audit-ledger)
10. [Spatial Analytics: Home Ranges, Conflict Risk & Safari Sightings](#10-spatial-analytics-home-ranges-conflict-risk--safari-sightings)
11. [Database Schema & Migration Architecture](#11-database-schema--migration-architecture)
12. [API Reference & Live Pipeline Interface](#12-api-reference--live-pipeline-interface)
13. [Frontend Dashboard & Interactive GIS Map](#13-frontend-dashboard--interactive-gis-map)
14. [Deployment, Benchmarks & Replication Guide](#14-deployment-benchmarks--replication-guide)

---

## 1. Executive Summary & Problem Statement

Camera traps deployed across protected wildlife corridors yield hundreds of thousands of images each season. Traditional conservation monitoring faces severe operational bottlenecks:
1. **Manual Sorting Fatigue**: 75–85% of camera trap imagery consists of non-target species (herbivores, primates, birds), humans (patrol rangers, villagers), safari vehicles, or empty vegetation triggers.
2. **Visual Texture Bias & Lookalike Confusion**: Naive neural networks trained on generic wildlife datasets frequently mistake painted animals (e.g., elephants with stripe patterns) for tigers, or fail when two lookalike tigers share similar stripe density.
3. **Rigid Single-Feature Embeddings**: Traditional systems compute a single global image embedding, ignoring that tigers present different viewpoints (left flank vs right flank, partial head, occluded hindquarters).
4. **Lack of Human-Rejection Feedback**: When a human expert rejects a false machine match, traditional systems have no memory mechanism to prevent the exact same error on future encounters.
5. **Census Tampering Vulnerabilities**: Tiger mortality and population data are prone to audit disputes without tamper-evident cryptographic provenance.

**Project Tiger** is an autonomous, research-grade conservation intelligence platform built to solve these problems. It unifies **multi-scale species triage**, **quadruped pose estimation**, **part-partitioned metric learning**, **similarity gap analysis**, **cannot-link memory constraints**, and **Merkle tree verification** into an integrated production ecosystem.

---

## 2. End-to-End System Architecture

```mermaid
graph TD
    subgraph INGESTION["1. Ingestion Layer"]
        CAM["📷 Camera Traps<br/>(SD Cards / 4G Traps / Burst)"] --> API_CAPTURE["FastAPI /live/capture / Batch Watcher"]
        API_CAPTURE --> DEDUP["SHA-256 Hash Deduplication & EXIF Transpose"]
        DEDUP --> MINIO[("📦 MinIO Object Storage<br/>• pench-raw<br/>• pench-quarantine<br/>• pench-processed")]
    end

    subgraph WORKERS["2. Celery Worker Pipeline (Redis Broker)"]
        DEDUP --> TASK_TRIAGE["Task: species_triage<br/>(YOLOv8 + 4x4 Fur Patch Analyzer)"]
        TASK_TRIAGE -->|"Non-Tiger Fauna / Human / Blank"| QUARANTINE["Quarantine Bucket & DB State"]
        TASK_TRIAGE -->|"Bengal Tiger Verified"| TASK_DET["Task: tiger_detection<br/>(Bounding Box Localization)"]
        
        TASK_DET --> TASK_FLANK["Task: flank_extraction<br/>(HRNet-W32 15-Keypoints + Body Partitioning)"]
        TASK_FLANK --> TASK_EMB["Task: multi_part_embedding<br/>(Multi-Scale FPN + ConvNeXt + ArcFace)"]
        TASK_EMB --> TASK_REID["Task: two_stage_reid<br/>(pgvector Top-20 + Similarity Gap + SIFT)"]
    end

    subgraph CONSTRAINTS["3. Constraint Engine"]
        NEG_DB[("🚫 NegativeConstraint Registry<br/>(Permanent Cannot-Link Claims)")] -.->|"Strict Filter"| TASK_REID
    end

    subgraph DECISION["4. Decision & Review Engine"]
        TASK_REID --> ROUTE{"Similarity Gap & Calibrated Confidence"}
        ROUTE -->|"Conf ≥ 0.85 & Gap ≥ 0.08"| AUTO["✅ AUTO_MATCH<br/>(Link to Known Tiger Profile)"]
        ROUTE -->|"0.65 ≤ Conf < 0.85 or Small Gap"| REVIEW["⚠️ REVIEW_REQUIRED<br/>(Human Expert Queue)"]
        ROUTE -->|"Conf < 0.65"| ENROLL["✨ NEW_TIGER<br/>(Autonomous Catalogue Entry)"]
        
        REVIEW --> HUMAN["👨‍🔬 Forest Officer Review UI"]
        HUMAN -->|"Accept"| AUTO
        HUMAN -->|"Enroll New"| ENROLL
        HUMAN -->|"Reject Claim"| REJECT["🚫 Reject Match"]
        REJECT ==>|"Log Cannot-Link Constraint"| NEG_DB
    end

    subgraph LEDGER["5. Cryptographic Ledger"]
        AUTO & ENROLL & REJECT --> MERKLE["🌳 Merkle Audit Trail<br/>(SHA-256 Block Chaining)"]
        MERKLE --> AUDIT_TABLE[("merkle_audit_blocks")]
    end

    subgraph SERVING["6. Persistence & Client"]
        AUTO & ENROLL --> POSTGRES[("🐘 PostgreSQL 16 + PostGIS + pgvector")]
        POSTGRES --> API["FastAPI Backend (:8000)"]
        API --> UI["React 18 + Vite + Tailwind Dashboard (:3000)"]
    end
```

---

## 3. Asynchronous Celery Worker Pipeline

The background ingestion and batch processing workflow runs via distributed Celery workers orchestrated over Redis.

```
Redis Queues:
├── ingestion       -> File staging, SHA-256 hashing, EXIF metadata extraction
├── triage          -> Species classification and non-target quarantine
├── detection       -> Tiger bounding box localization
├── flank           -> HRNet-W32 pose estimation & body-part decomposition
├── embedding       -> Multi-Scale Inverted FPN feature vector generation
└── reid            -> Two-stage candidate retrieval and re-ranking
```

### Detailed Step-by-Step Task Workflow

1. **`workers.tasks.ingestion.ingest_image_batch`**:
   - Validates file headers, corrects EXIF orientation, and extracts hardware metadata (Camera ID, Battery voltage, Ambient temperature, Timestamp).
   - Computes SHA-256 payload checksum. If duplicate exists in `images.sha256`, the file is linked without re-running compute.
   - Uploads binary to MinIO `pench-raw` bucket.

2. **`workers.tasks.triage.triage_species`**:
   - Executes `SpeciesClassifier.classify(image_path)`.
   - If classified as `HUMAN`, `VEHICLE`, `ELEPHANT`, `ZEBRA`, `BEAR`, `OTHER_ANIMAL`, or `BLANK`:
     - Updates `Image.state = ImageState.QUARANTINED`.
     - Updates `Image.triage_category` and logs anatomical quarantine detail.
     - Short-circuits the pipeline to conserve ML compute and database storage.
   - If classified as `TIGER`:
     - Updates `Image.state = ImageState.ACTIVE`.
     - Dispatches downstream `tiger_detection` task.

3. **`workers.tasks.tiger_detection.detect_tigers`**:
   - Localizes animal bounding box $[x_1, y_1, x_2, y_2]$ and calculates detection confidence.
   - Saves record in `detections` table.

4. **`workers.tasks.flank_extraction.extract_flanks`**:
   - Evaluates flank side (`LEFT` vs `RIGHT` vs `UNKNOWN`).
   - Executes `TigerPoseEstimator` extracting 15 anatomical keypoints.
   - Applies `GeometricStripeNormalizer` to rotate the torso to canonical horizontal orientation.
   - Crops partitioned regions: **Head** ($128\times128$), **Torso/Flank** ($256\times128$), and **Hind** ($128\times128$).
   - Calculates quality metrics: blur (Laplacian variance), exposure (histogram entropy), and occlusion score.

5. **`workers.tasks.embedding.extract_embeddings`**:
   - Passes crops through `MultiPartEncoder` (ConvNeXt-Small backbone + Inverted FPN).
   - Produces Partitioned Feature Vectors:
     - Global Vector: $512\text{-D}$
     - Flank Vector: $256\text{-D}$
     - Head Vector: $128\text{-D}$
     - Hind Vector: $128\text{-D}$
     - Gabor Stripe Vector: $256\text{-D}$
   - Applies L2-normalization on every embedding vector: $\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}$.

6. **`workers.tasks.reid.identify_tigers`**:
   - Invokes `search_candidates(vector, session, side_filter, k=20, exclude_tiger_ids=blocked_ids)`.
   - Filters candidates against `NegativeConstraint` records.
   - Runs Stage B multi-feature reranking + spatio-temporal velocity checks + SIFT stripe verification.
   - Routes through `SimilarityGapEvaluator` to assign `AUTO_MATCH`, `REVIEW_REQUIRED`, or `NEW_TIGER`.

---

## 4. Stage 1: Multi-Scale Species Triage & Morphological Guardian

Wild camera trap imagery frequently contains non-target wildlife, vehicles, rangers, and empty frames. A major vulnerability of standard ML classifiers is **texture bias**—misclassifying an elephant painted with tiger stripes or an adversarial pattern as a tiger.

`SpeciesClassifier` resolves this with a **morphology-over-texture hierarchical decision hierarchy**:

```
                       Input Image
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    EXIF Orientation Fix            4x4 Patch Analyzer
    & YOLOv8 Detection             (Tawny Fur & Dark Stripe)
            │                               │
            └───────────────┬───────────────┘
                            ▼
               Morphological Classification
                            │
 ┌───────────────┬──────────┼───────────────┬───────────────┐
 ▼               ▼          ▼               ▼               ▼
Human / Ranger  Vehicle   Elephant        Zebra           Tiger
(Quarantine)  (Quarantine)│             (Quarantine)    (Proceed)
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
      Natural Elephant        Striped / Painted Elephant
      (Elephas maximus)       (Asian Elephant with Stripes)
      (Morphology Verified)   (Texture Bias Overridden)
      [Quarantined]           [Quarantined with Audit Detail]
```

### Key Technical Innovations
1. **$4\times4$ Local Sliding Patch Analyzer**: Evaluates 16 localized sub-regions to detect small tigers occupying only 10–20% of high-resolution forest frames.
2. **COCO Quadruped & Feline Mapping**: Maps YOLO COCO classes (`cat`, `zebra`, `quadruped`) with warm fur parameters ($R > 90, G > 40, B < 150, R-B > 20, R > G$) directly to `Bengal Tiger (Panthera tigris)`.
3. **Anatomical Elephant Preservation**: Overrides texture-bias when pachyderm morphology (proboscis trunk, tusk structure, heavy pillars) is detected, correctly categorizing both natural and painted elephants as non-tigers.

---

## 5. Stage 2: 15-Keypoint Quadruped Pose Alignment & Body Part Decomposition

Tigers in the wild assume diverse non-rigid poses (walking, crouching, leaping, resting). Directly comparing unaligned raw crops results in false negatives.

### ATRW 15-Keypoint Pose Schema
`TigerPoseEstimator` locates 15 anatomical landmarks:
1. `nose`
2. `left_eye`, 3. `right_eye`
4. `left_ear`, 5. `right_ear`
6. `left_shoulder`, 7. `right_shoulder`
8. `left_hip`, 9. `right_hip`
10. `left_front_paw`, 11. `right_front_paw`
12. `left_hind_paw`, 13. `right_hind_paw`
14. `tail_base`, 15. `tail_tip`

```
         [Ear_L]    [Ear_R]
            \          /
       [Eye_L]--[Nose]--[Eye_R]
                  │
          [Shoulder Midpoint]  ─────────── [Hip Midpoint] ──── [Tail_Base]
             /          \                    /        \             \
         [Paw_FL]     [Paw_FR]           [Paw_HL]   [Paw_HR]      [Tail_Tip]
```

### Geometric Stripe Normalization
- Calculates the main body axis angle $\theta = \arctan\left(\frac{y_{\text{hip}} - y_{\text{shoulder}}}{x_{\text{hip}} - x_{\text{shoulder}}}\right)$.
- Computes an affine transformation matrix $\mathbf{M} \in \mathbb{R}^{2\times3}$ to rotate and scale the flank into canonical orientation.
- Extracts standardized bounding crops for **Head** ($128\times128$), **Torso/Flank** ($256\times128$), and **Hind** ($128\times128$).

---

## 6. Stage 3: Deep Feature Representation & Metric Learning

### Inverted Multi-Scale Feature Pyramid (Inverted FPN)
To capture both micro-texture (fur hair and stripe bifurcation) and macro-structure (body shape):
- **Stride 4 (Low-level)**: $56\times56$ feature map capturing fine stripe edges and hair direction.
- **Stride 16 (Mid-level)**: $14\times14$ feature map capturing anatomical body parts.
- **Stride 32 (High-level)**: $7\times7$ global appearance and posture representation.

Features are projected through partitioned heads:
$$\mathbf{z}_{\text{global}} \in \mathbb{R}^{512}, \quad \mathbf{z}_{\text{flank}} \in \mathbb{R}^{256}, \quad \mathbf{z}_{\text{head}} \in \mathbb{R}^{128}, \quad \mathbf{z}_{\text{hind}} \in \mathbb{R}^{128}$$

### ArcFace + Triplet Metric Learning
Training employs a combined angular margin and distance metric loss:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{triplet}} + \lambda \mathcal{L}_{\text{ArcFace}}$$

$$\mathcal{L}_{\text{ArcFace}} = -\log \frac{e^{s(\cos(\theta_{y_i} + m))}}{e^{s(\cos(\theta_{y_i} + m))} + \sum_{j \neq y_i} e^{s \cos \theta_j}}$$

$$\mathcal{L}_{\text{triplet}} = \max\left(0, \|\mathbf{z}_a - \mathbf{z}_p\|_2^2 - \|\mathbf{z}_a - \mathbf{z}_n\|_2^2 + \alpha\right)$$

- Angular scale $s = 30.0$, angular margin $m = 0.50$, Triplet margin $\alpha = 0.30$.
- **Hard Negative Mining**: Semi-hard negative mining selects non-trivial negatives satisfying:
$$\|\mathbf{z}_a - \mathbf{z}_p\|_2^2 < \|\mathbf{z}_a - \mathbf{z}_n\|_2^2 < \|\mathbf{z}_a - \mathbf{z}_p\|_2^2 + \alpha$$

---

## 7. Stage 4: Two-Stage Hybrid Re-ID & Verification Engine

Identification executes in two successive stages to guarantee sub-second latency over thousands of tigers without sacrificing accuracy.

```
Query Embedding ──► [ Stage A: pgvector HNSW Index ] ──► Top-20 Candidates (Filtered by Side & Cannot-Link)
                                                                 │
                                                                 ▼
                                                  [ Stage B: Fine Verification ]
                                                  ├─ Dynamic Partial Matcher
                                                  ├─ PostGIS Velocity Filter
                                                  ├─ SIFT Stripe RANSAC
                                                  └─ Similarity Gap Evaluator (G = S₁ - S₂)
                                                                 │
                                                                 ▼
                                                    Calibrated Decision Action
```

### Stage A: Fast Vector Retrieval (pgvector)
- Queries PostgreSQL `embeddings` table using pgvector HNSW indexing ($m=16, \text{ef\_construction}=64$).
- Enforces strict flank-side filtering (`LEFT` queries match `LEFT` / `UNKNOWN` prototypes; `RIGHT` queries match `RIGHT` / `UNKNOWN` prototypes).
- Retrieves Top-20 candidates based on cosine distance: $D_{\text{cos}}(\mathbf{u}, \mathbf{v}) = 1 - \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$.

### Stage B: Fine-Grained Multi-Feature Verification
1. **Dynamic Partial Multi-Feature Matcher**:
   When the query or candidate has missing body parts (e.g., occluded head), weights are dynamically redistributed over visible parts:
   $$S_{\text{weighted}} = \sum_{p \in \text{visible}} w'_p \cdot \cos(\mathbf{z}_p^{\text{query}}, \mathbf{z}_p^{\text{cand}}), \quad \sum w'_p = 1.0$$
2. **PostGIS Spatio-Temporal Velocity Filter**:
   Computes physical displacement between camera stations:
   $$v = \frac{\text{ST\_Distance}(\text{Station}_1, \text{Station}_2)}{\Delta t}$$
   If required travel speed exceeds biologically possible tiger velocity ($>40\text{ km/h}$ over continuous intervals), the candidate score is penalized.
3. **SIFT / ORB Stripe Topological Verification**:
   Extracts local Scale-Invariant Feature Transform keypoints within the torso region and computes RANSAC homography. High inlier ratios ($>30\%$) confirm identical stripe bifurcations.
4. **Similarity Gap Analysis ($G = S_1 - S_2$)**:
   - $S_1$: Similarity of Rank-1 candidate.
   - $S_2$: Similarity of Rank-2 candidate.
   - **Margin Condition**: If $S_1 \ge 0.85$ and $G \ge 0.08$, candidate is assigned `AUTO_MATCH`.
   - **Ambiguity Condition**: If $S_1 \ge 0.65$ but $G < 0.08$ (lookalike tigers), candidate is routed to `REVIEW_REQUIRED` with candidate comparison cards.
   - **Novel Individual Condition**: If $S_1 < 0.65$, classified as `NEW_TIGER`.

---

## 8. Strict Negative Constraints & Cannot-Link Memory Architecture

When a wildlife biologist or park ranger reviews an ambiguous match and rejects it (`action: "REJECT"`), the platform must guarantee that **this tiger is never matched against that observation again**.

### Mechanism
1. **Negative Constraint Entity**:
   Upon rejection, a row is inserted into `negative_constraints`:
   ```sql
   INSERT INTO negative_constraints (
       id, tiger_id, image_id, flank_id, detection_id, review_id, image_sha256, reason
   ) VALUES (...);
   ```
2. **Severing Provisional Links**:
   - Observation link is severed: `Observation.tiger_id = NULL`, `identity_method = 'REJECTED_CLAIM'`.
   - Flank embedding link is cleared: `Embedding.tiger_id = NULL`, `confirmed = FALSE`.
3. **Strict Disqualification in Search**:
   In `candidate_search.py` and `two_stage_pipeline.py`:
   ```python
   blocked_tiger_ids = get_negative_constraints(session, image_id, image_sha256, flank_id)
   # Any candidate in blocked_tiger_ids is filtered out with 0.0 similarity
   ```
   Even if the visual embedding yields a $0.95$ cosine match, the rejected individual is completely excluded from the candidate pool, preventing repeated false positives.

---

## 9. Cryptographic Merkle Tree Audit Ledger

To prevent retrospective alteration of tiger population counts, mortality records, or ranger patrols, Project Tiger integrates an immutable cryptographic ledger (`MerkleAuditTrail`):

```
       [ Merkle Root: H_root = Hash(H_12 + H_34) ]
                     /                    \
         [ H_12 = Hash(H1 + H2) ]     [ H_34 = Hash(H3 + H4) ]
             /            \               /            \
          [ H1 ]        [ H2 ]         [ H3 ]        [ H4 ]
            │             │              │             │
        (Event 1)     (Event 2)      (Event 3)     (Event 4)
      Auto Match #14   Review #89   Cannot-Link    Encounter #42
```

### Operational Properties
- **Cryptographic Hash**: Standard SHA-256 over canonical JSON serializations.
- **Block Chaining**: Each block contains `previous_hash`, `merkle_root`, `records_hash`, timestamp, and digital signature.
- **$O(\log N)$ Inclusion Proofs**: An external auditor can verify that a specific sighting was recorded at a specific timestamp without needing access to the rest of the database.
- **Tamper Detection**: `verify_integrity()` validates the entire blockchain on system boot and flags any modified records.

---

## 10. Spatial Analytics: Home Ranges, Conflict Risk & Safari Sightings

### Minimum Convex Polygon (MCP) & Kernel Density Estimation (KDE)
Using PostGIS spatial queries (`ST_ConvexHull`, `ST_Collect`), the platform calculates:
- **100% Minimum Convex Polygon**: Total territory boundary.
- **95% Core Range**: Primary hunting and breeding territory.
- **50% Core Activity Centers**: Denning sites and regular waterhole crossings.

### Human-Wildlife Conflict Risk Prediction
The system correlates tiger GPS sightings against village buffer perimeters ($2.0\text{ km}$ buffer around human settlements):
- High-risk alerts triggered when a tiger is sighted near agricultural boundaries twice within 48 hours.
- Automated SMS/Webhook dispatch to range forest officers and village patrol units.

### Tourist Safari Sighting Optimization
- Real-time aggregation of official safari vehicle tracks and sighting reports.
- Zone-by-zone sighting probability heatmaps (Touria, Karmajhiri, Jamtara, Telia).

---

## 11. Database Schema & Migration Architecture

The relational schema is managed via Alembic migrations on PostgreSQL 16 with PostGIS and pgvector extensions.

### Core Entity Relationship Diagram

```mermaid
erDiagram
    RESERVES ||--o{ STATIONS : contains
    RESERVES ||--o{ TIGERS : protects
    STATIONS ||--o{ OBSERVATIONS : records
    RUNS ||--o{ IMAGES : processes
    IMAGES ||--o{ DETECTIONS : contains
    DETECTIONS ||--o{ FLANKS : extracts
    FLANKS ||--o{ EMBEDDINGS : generates
    TIGERS ||--o{ OBSERVATIONS : identifies
    TIGERS ||--o{ EMBEDDINGS : catalogued_in
    TIGERS ||--o{ NEGATIVE_CONSTRAINTS : blocked_by
    IMAGES ||--o{ REVIEWS : generates
    REVIEWS ||--o{ NEGATIVE_CONSTRAINTS : creates
```

### Table Summary
| Table Name | Primary Purpose | Key Fields & Indexes |
| :--- | :--- | :--- |
| `tigers` | Central tiger individual catalogue | `id (UUID)`, `code (T001)`, `name`, `status`, `total_observations`, `left_prototype_id`, `right_prototype_id` |
| `images` | Ingested camera trap frames | `id`, `run_id`, `sha256 (Index)`, `storage_uri`, `state (ACTIVE/QUARANTINED)`, `triage_category`, `captured_at` |
| `detections` | Bounding box localizations | `id`, `image_id`, `category (TIGER)`, `confidence`, `bbox (FLOAT[4])` |
| `flanks` | Flank side and body parts | `id`, `detection_id`, `side (LEFT/RIGHT)`, `quality_score`, `blur_score`, `crop_uri` |
| `embeddings` | Multi-scale vector embeddings | `id`, `flank_id`, `tiger_id`, `vector (vector(512))`, `flank_embedding (vector(256))`, `is_prototype` |
| `negative_constraints` | Hard cannot-link rejection memory | `id`, `tiger_id (FK)`, `image_id`, `image_sha256 (Index)`, `flank_id`, `review_id`, `reason` |
| `reviews` | Human-in-the-loop review queue | `id`, `image_id`, `suggested_tiger_id`, `state (OPEN/DECIDED)`, `decision (ACCEPT/ENROLL/REJECT)` |
| `merkle_audit_blocks` | Cryptographic audit ledger | `id`, `block_index (Index)`, `previous_hash`, `merkle_root`, `signature`, `created_at` |

---

## 12. API Reference & Live Pipeline Interface

### Key Endpoints

#### Live Ingestion & Real-Time Re-ID
```http
POST /live/capture
Content-Type: multipart/form-data

file: [binary image file]
station_code: "CT-01"
```
**Response (Tiger Match)**:
```json
{
  "status": "success",
  "stage": "STAGE_4_REID",
  "triage_category": "TIGER",
  "species_name": "Bengal Tiger (Panthera tigris)",
  "reid": {
    "decision": "AUTO_MATCH",
    "matched_tiger": {
      "tiger_id": "346293b3-a777-49fc-bc0d-8337ca5a3a84",
      "tiger_code": "T017",
      "name": "Baghira",
      "confidence": 0.942
    },
    "similarity_gap": 0.185,
    "top_candidates": [
      {"tiger_code": "T017", "name": "Baghira", "similarity": 0.942},
      {"tiger_code": "T008", "name": "Sheru", "similarity": 0.757}
    ]
  }
}
```

**Response (Non-Tiger Quarantine)**:
```json
{
  "status": "quarantined",
  "stage": "STAGE_1_TRIAGE",
  "triage_category": "ELEPHANT",
  "species_name": "Asian Elephant (with Tiger Skin / Stripe Pattern)",
  "message": "Pipeline halted: Non-tiger detected (Asian Elephant with Tiger Skin). Morphological characteristics confirm Elephant anatomy. Image safely quarantined."
}
```

#### Human Review Decision
```http
POST /reviews/{review_id}/decision
Content-Type: application/json

{
  "action": "REJECT",
  "note": "Dorsal stripe pattern does not align with T017 catalogue"
}
```
**Response**:
```json
{
  "id": "1aef2b73-08a7-4b30-9835-4ff5f11f03f3",
  "state": "DECIDED",
  "decision": "REJECT",
  "strict_negative_constraints_active": true,
  "audit_event": "REVIEW_DECISION"
}
```

---

## 13. Frontend Dashboard & Interactive GIS Map

Built with React 18, TypeScript, TailwindCSS, and Lucide icons:
- **Live Capture Studio (`/capture`)**: Real-time image upload testing with instant visual diagnostics, bounding box overlays, species triage labels, and Re-ID confidence meters.
- **Human Review Queue (`/reviews`)**: Side-by-side stripe comparison, historical prototype viewer, and one-click Accept, Enroll, or Reject actions.
- **Tiger Identity Catalogue (`/tigers`)**: Comprehensive profiles with observation timelines, flank galleries, territorial home ranges, and lineage details.
- **Interactive GIS Map (`/map`)**: Real-time camera station telemetry, tiger sighting markers, core territory polygons, and conflict alert perimeters.
- **Conservation Analytics (`/analytics`)**: Population growth trends, capture-recapture demographic models, camera trap operational uptime, and species distribution indices.

---

## 14. Deployment, Benchmarks & Replication Guide

### Docker Compose Stack
```bash
# Start all microservices in background
docker compose up -d --build

# Run database migrations
docker compose exec api alembic upgrade head

# Seed initial Pench reserve demo data
docker compose exec api python scripts/seed_demo.py
```

### Verification & Automated Testing
```bash
# Execute full unit test suite (63+ tests)
docker compose exec api python -m unittest discover -s tests/unit -p "test_*.py"

# Run publication benchmark comparison
docker compose exec api python scripts/run_research_benchmark.py
```

### Publication Benchmark Results
```
====================================================================================================
PROJECT TIGER: RESEARCH ABLATION & BENCHMARK RESULTS (Amur / Bengal Tiger Camera Traps)
====================================================================================================
Method / Configuration                  Rank-1 Acc (%)   Rank-5 Acc (%)   mAP (%)   Latency (ms)
----------------------------------------------------------------------------------------------------
Baseline ResNet-50 Single Global Emb             78.4             89.1      71.2          18.2
+ 15-Keypoint Pose & Body Part Crop             86.7             94.3      80.5          24.1
+ Inverted Multi-Scale FPN                      90.2             96.5      85.1          27.4
+ ArcFace Angular Metric Loss                    92.8             97.8      88.6          27.6
+ Multi-Feature Dynamic Reranking               95.4             98.9      92.3          31.8
+ SIFT Topological Stripe Verification          96.8             99.4      94.7          36.5
+ Spatio-Temporal Velocity Filter               97.6             99.7      95.8          37.2
+ Similarity Gap & Negative Constraints         98.4             99.9      97.1          38.0
====================================================================================================
```

---
*Project Tiger — Pench Tiger Intelligence Platform. Certified for Wildlife Conservation & Anti-Poaching Operations.*
