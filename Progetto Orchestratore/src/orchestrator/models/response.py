from pydantic import BaseModel
from typing import List
from .job import JobItem

class ExtractRequest(BaseModel):
    job_title: str
    city: str

class ExtractResponse(BaseModel):
    job_title: str
    city: str
    count: int
    report_path: str | None = None
    items: List[JobItem]