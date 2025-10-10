from pydantic import BaseModel, HttpUrl

class JobItem(BaseModel):
    title: str
    company: str | None = None
    city: str | None = None
    url: HttpUrl | None = None
    source: str | None = None