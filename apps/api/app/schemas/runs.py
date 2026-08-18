from datetime import datetime
from pydantic import BaseModel, Field

class RunCreate(BaseModel):
    source_directory: str = Field(description="Directory below configured raw storage root")
    station_code: str | None = None

class RunSummary(BaseModel):
    id: str
    status: str
    created_at: datetime
    total_images: int = 0
    retained_images: int = 0
    quarantined_images: int = 0
    quarantined_bytes: int = 0
    review_required: int = 0
