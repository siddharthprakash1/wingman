from pydantic import BaseModel
from typing import List

class CitedAnswer(BaseModel):
    answer_text: str
    source_citations: List[str] = []
    confidence_scores: List[float] = []
