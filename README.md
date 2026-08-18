# Pench Tiger Intelligence — AI-Powered Wildlife Telemetry Platform

An enterprise-grade, multi-service AI surveillance platform designed for camera-trap triage, open-set tiger Re-Identification (Re-ID), spatial telemetry analytics, and anomaly alerting. Built for high-throughput conservation monitoring at Pench Reserve.

> [!NOTE]
> **Hackathon Demonstration Notice**: To protect wild populations from poaching, all spatial coordinates, tiger identities, and alert notifications in this demonstration are **synthetic**.

---

## 🛠 Tech Stack & Architecture

Pench Tiger Intelligence is built as a highly modular, decoupled system to support real-time edge processing and heavy async workloads:

- **Frontend**: React 18 (Vite, TypeScript) + Tailwind CSS + Three.js 3D Viewport (Sci-Fi Reserve Telemetry).
- **Backend API**: FastAPI (Python 3.12) + SQLAlchemy (Synchronous connection pooling).
- **Database**: PostgreSQL 16 + **PostGIS** (spatial geometry querying) + **pgvector** (vector search for Re-ID).
- **Async Workers**: Celery + Redis (broker) for background image processing, model inference, and spatial updates.
- **Object Storage**: MinIO (S3-compatible API) for raw files, quarantine, and cropped flanks.

```
                    ┌─────────────────────────┐
                    │  React Web Dashboard    │
                    └───────────┬─────────────┘
                                │ (HTTP / JWT)
                                ▼
                    ┌─────────────────────────┐
                    │   FastAPI Gateway API   │
                    └───────────┬─────────────┘
                                │ (Celery Task Dispatch)
                                ▼
  ┌───────────────┬─────────────┼───────────────┬───────────────┐
  ▼               ▼             ▼               ▼               ▼
┌───────────┐   ┌───────────┐ ┌───────────┐   ┌───────────┐   ┌───────────┐
│ Ingest    │ ─>│ Triage    │ │ Detection │ ─>│ Re-ID     │ ─>│ Spatial   │
│ Task      │   │ Task      │ │ Task      │   │ Task      │   │ & Alerts  │
└─────┬─────┘   └─────┬─────┘ └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
      │               │             │               │               │
      ▼ (Write Metadata & Geometry) ▼ (Vector Query)▼               ▼
┌───────────────────────────────────────────────────────────────────────┐
│              PostgreSQL (PostGIS + pgvector) / MinIO                  │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 How to Run the Project (Step-by-Step)

The project includes a `Makefile` for streamlined environment control.

### Prerequisites
- **Docker Desktop** installed and running on your system.
- **Python 3.12+** (for running local scripts/servers).

---

### Step 1: Initialize Infrastructure
1. Copy the environment variables:
   ```bash
   cp .env.example .env
   ```
2. Start the core database, cache, and object storage servers in the background:
   ```bash
   make up
   ```
   *This starts Postgres/PostGIS/pgvector, Redis, MinIO, and sets up S3 buckets automatically.*

---

### Step 2: Set Up Local Virtual Environment (For Local Dev & Tests)
If you wish to run the servers locally:
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # On Windows
   source .venv/bin/activate # On Unix
   ```
2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r apps/api/requirements.txt
   pip install pytest pytest-asyncio
   ```

---

### Step 3: Run Database Migrations & Seeding
Create the database tables and populate the system with realistic demo data:
1. Run Alembic migrations:
   ```bash
   make db-migrate
   ```
2. Seed the database (creates demo camera stations, tiger individuals, and historical logs):
   ```bash
   make db-seed
   ```
   *Demo credentials: email: `riya@pench.gov.in`, password: `demo2026`*

---

### Step 4: Run the Application Services
Run these in separate terminal windows:
- **FastAPI Backend Server**:
  ```bash
  make api
  ```
  *(Runs at http://localhost:8000. API Docs at http://localhost:8000/docs)*
- **Celery Processing Worker**:
  ```bash
  make worker
  ```
- **React Frontend Dashboard**:
  ```bash
  make frontend
  ```
  *(Access the gorgeous dashboard at http://localhost:5173)*

---

### Step 5: Verify the Build (Run Tests)
Ensure all systems are functioning properly:
```bash
make test
```

---

## 🧬 Training Data & Machine Learning Pipeline

As an international hackathon submission, this system implements an **Open-Set Re-Identification** architecture that solves a critical real-world problem: **Tigers cannot be trained on standard classification models because new individuals are constantly discovered in the wild.**

### 1. Ingestion & Triage (MegaDetector V6)
- **What it does**: Automatically removes blank frames (wind, branches) to save up to 60%+ of storage costs.
- **How to test**: Drop camera-trap images into `storage/raw/`. Create a new Ingestion Run from the frontend. The worker will trigger the triage task and quarantine blank images.
- **Weights**: Pre-trained MegaDetector V6 weights are loaded automatically on the worker container via `PytorchWildlife`.

### 2. Flank Feature Extraction (ResNet50 / Custom Encoders)
- **What it does**: Extracts a 512-dimensional vector embedding representing the tiger's stripe pattern from left or right flank crops.
- **Custom Training**:
  - The model architecture is defined in [`ml/reid/embedding.py`](file:///d:/project%20tiger/ml/reid/embedding.py).
  - To train a custom Re-ID model, compile a dataset of cropped stripe images (organized by tiger ID) under [`datasets/raw/`](file:///d:/project%20tiger/datasets/raw).
  - Fine-tune a Siamese or Triplet Loss network, export the weights to `models/checkpoints/`, and update the `extract_embedding` function in `embedding.py` to point to your new weights.

### 3. Open-Set Enrollment (pgvector)
- When a tiger is detected, its embedding is checked against the database:
  - **Auto-Match**: If similarity exceeds the configured auto-match threshold (e.g. `0.90`) with a clear margin, it is automatically assigned.
  - **Review Queue**: If the similarity is ambiguous (e.g., `0.76` or multiple matches close together), it is routed to the **Human-in-the-Loop Review Queue**.
  - **Enrollment**: The investigator reviews the side-by-side flank similarity comparison in the dashboard and can choose to **Enroll as a New Tiger** or confirm a candidate. Enrolling appends the vector to pgvector, updating the system in real-time without retraining!

### 4. PostGIS Spatial Intelligence & Alerts
- Observations are saved as PostGIS point geometries.
- Minimum Convex Polygon (MCP) range areas are computed dynamically using a Monotone Convex Hull algorithm in [`spatial/mcp.py`](file:///d:/project%20tiger/spatial/mcp.py).
- The alert engine (`alerts/engine.py`) continuously evaluates:
  - **Buffer Entry**: Core-to-Buffer boundary crossing.
  - **Extended Absence**: Warning if an individual is missing for over 30 days.
  - **Station Novelty**: Unexpected appearances at new camera locations.
