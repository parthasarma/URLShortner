from pydantic import BaseModel, HttpUrl

class ShortenRequest(BaseModel):
    url: HttpUrl

class ShortenResponse(BaseModel):
    code: str
    short_url: str
    long_url: str
    created_at: str

class LookupRequest(BaseModel):
    short: str

class LookupResponse(BaseModel):
    code: str
    long_url: str
    created_at: str
