"""Temporary in-memory repository for the demo API.

Replace this module with SQLAlchemy/PostGIS repositories once the database
migration layer is enabled. It centralizes state so API route modules do not
invent conflicting records.
"""
from datetime import datetime, timezone
from uuid import uuid4

class DemoRepository:
    def __init__(self):
        self.tigers = [
            {"id":"T017","name":"Baghira","sex":"male","confidence":.92,"observations":14,"range_sq_km":18.6,"status":"confirmed"},
            {"id":"T021","name":"Tara","sex":"female","confidence":.88,"observations":9,"range_sq_km":12.1,"status":"confirmed"},
            {"id":"T008","name":"Sheru","sex":"male","confidence":.96,"observations":22,"range_sq_km":24.8,"status":"confirmed"},
        ]
        self.alerts = [{"id":"ALT-204","type":"buffer_entry","tiger_id":"T017","severity":"critical","status":"created","evidence_count":3,"rule_version":"alerts-v1"}]
        self.reviews = [{"id":"REV-001","state":"OPEN","image_id":"IMG-DEMO-001","candidates":[{"tiger_id":"T017","similarity":.76},{"tiger_id":"T021","similarity":.71}],"created_at":datetime.now(timezone.utc).isoformat()}]
        self.observations = [{"id":"OBS-001","tiger_id":"T017","station_id":"P-18","captured_at":"2026-08-11T05:42:00Z","identity_confidence":.92,"geometry":[79.28,21.73],"synthetic":True}]
        self.audit_log: list[dict] = []

    def audit(self, event: str, actor: str = "demo-user", **data):
        self.audit_log.append({"id":str(uuid4()),"event":event,"actor":actor,"at":datetime.now(timezone.utc).isoformat(),**data})

repository = DemoRepository()
