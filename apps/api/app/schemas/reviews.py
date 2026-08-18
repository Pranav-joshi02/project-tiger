from typing import Literal
from pydantic import BaseModel, Field

class ReviewDecision(BaseModel):
    action: Literal["ACCEPT_CANDIDATE", "ENROLL_NEW", "REJECT"]
    tiger_id: str | None = None
    note: str = Field(default="", max_length=1000)
