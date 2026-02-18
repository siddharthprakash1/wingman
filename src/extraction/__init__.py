"""
Extraction Module - Structured information extraction using LangExtract.

LangExtract is Google's open-source library for extracting structured 
information from unstructured text using LLMs with source grounding.

Features:
- Schema-based extraction with few-shot examples
- Source grounding (maps extractions to exact text locations)
- Multi-provider support (Gemini, OpenAI, Ollama)
- Long document processing with chunking
- Interactive visualization
"""

from src.extraction.extractor import (
    Extractor,
    ExtractionSchema,
    ExtractionResult,
    extract_entities,
    extract_structured_data,
)

__all__ = [
    "Extractor",
    "ExtractionSchema",
    "ExtractionResult",
    "extract_entities",
    "extract_structured_data",
]
