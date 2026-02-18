from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class DocumentMetadata(BaseModel):
    title: str
    author: Optional[str] = None
    date: Optional[date] = None
    topics: List[str] = []
