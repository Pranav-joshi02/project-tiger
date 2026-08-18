# API

All endpoints are prefixed at the service root (`http://localhost:8000`).

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/runs` | Safely ingest a directory beneath `storage/raw` and start triage. |
| `GET` | `/runs/{id}` | Read run status and reversible-triage metrics. |
| `POST` | `/runs/{id}/restore` | Mark all quarantined images in a run as restored. |
| `POST` | `/images/upload` | Upload raw camera-trap images into a new immutable batch. |
| `GET` | `/dashboard` | Synthetic dashboard summary. |
| `GET` | `/tigers` | Synthetic tiger catalogue. |
| `GET/POST` | `/reviews`, `/reviews/{id}/decision` | Read ambiguous identities and record audited decisions. |
| `GET/PATCH` | `/alerts`, `/alerts/{id}` | List and update alert lifecycle state. |
| `GET` | `/maps/observations.geojson` | Role-safe, synthetic observation geometry. |
| `GET` | `/reports/tigers.csv` | Download a tiger catalogue report. |

The current `POST /runs` payload is `{ "source_directory": "demo-batch" }`. Path traversal and arbitrary host paths are rejected.
