from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = None

class QueryResponse(BaseModel):
    result: Optional[str] = None
    error: Optional[str] = None