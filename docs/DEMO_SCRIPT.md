# First Milestone Demo

1. Copy a test folder below `storage/raw/`.
2. On the first run, MegaDetector V6 weights download automatically through PytorchWildlife. Confirm your deployment has network access or pre-warm the model image.
3. `POST /runs` with `{ "source_directory": "demo-batch" }`.
4. Show totals, duplicate count, retained frames, and quarantined byte count.
5. `POST /runs/{id}/restore` to demonstrate reversibility.

The API uses MegaDetector V6, currently the MIT-licensed compact YOLOv9 variant. Its initial thresholds must be calibrated on a labelled Pench-like validation sample before operational deployment. Any model-load or inference failure produces `REVIEW_REQUIRED`, never automatic quarantine.
