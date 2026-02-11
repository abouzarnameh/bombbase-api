from pydantic import BaseModel, Field

class PendingSimpleReq(BaseModel):
    creator_id: int

class AddItemReq(BaseModel):
    title: str | None = None
    travel_ms: int = Field(..., gt=0)
    priority: int = Field(1, ge=1)

class SessionOut(BaseModel):
    id: int
    creator_id: int
    status: str
    created_at_ms: int

class ItemOut(BaseModel):
    id: int
    session_id: int
    title: str | None
    travel_ms: int
    priority: int
    created_at_ms: int

class SessionBundleOut(BaseModel):
    session: dict
    items: list[dict]
