from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GlobalSearchResultItem(BaseModel):
    id: str
    entity_type: str  # "lead" | "client" | "conversation" | "message"
    title: str
    subtitle: Optional[str] = None
    snippet: Optional[str] = None
    url: str
    metadata: Dict[str, Any] = {}


class GlobalSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[GlobalSearchResultItem]
