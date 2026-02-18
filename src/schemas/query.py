from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class QueryIntent(BaseModel):
    filters: Optional[dict] = None
    temporal_constraints: Optional[date] = None
    entities: List[str] = []
