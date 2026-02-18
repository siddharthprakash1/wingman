"""
Extraction Tools - Structured data extraction using LangExtract.

Provides tools for extracting structured information from text
using Google's LangExtract library with LLM-powered extraction.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


async def extract_entities_from_text(
    text: str,
    entity_types: str,
    model: str = "gemini-2.5-flash",
) -> str:
    """
    Extract entities from text using LangExtract.
    
    Args:
        text: The text to extract from
        entity_types: Comma-separated entity types (e.g., "person, organization, location")
        model: LLM model to use (default: gemini-2.5-flash)
        
    Returns:
        JSON string of extracted entities with source grounding
    """
    try:
        from src.extraction.extractor import Extractor
    except ImportError:
        return (
            "❌ LangExtract not available. Install with:\n"
            "pip install langextract"
        )
    
    try:
        extractor = Extractor(model_id=model)
        entity_list = [e.strip() for e in entity_types.split(",")]
        
        prompt = f"""Extract all entities of the following types from the text:
{', '.join(entity_list)}

For each entity, identify:
- The exact text as it appears
- The entity type
- Any relevant attributes (e.g., role, relationship, description)"""
        
        result = extractor.extract(text, prompt)
        
        if result.success:
            return json.dumps({
                "success": True,
                "entity_count": len(result.extractions),
                "entities": result.extractions,
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result.error,
            }, indent=2)
            
    except Exception as e:
        return f"❌ Extraction failed: {e}"


async def extract_structured_info(
    text: str,
    schema_description: str,
    model: str = "gemini-2.5-flash",
) -> str:
    """
    Extract structured information according to a schema.
    
    Args:
        text: The text to extract from
        schema_description: Description of what to extract and expected structure
        model: LLM model to use
        
    Returns:
        JSON string of extracted structured data
    """
    try:
        from src.extraction.extractor import Extractor
    except ImportError:
        return (
            "❌ LangExtract not available. Install with:\n"
            "pip install langextract"
        )
    
    try:
        extractor = Extractor(model_id=model)
        
        prompt = f"""Extract structured information from the text according to this schema:

{schema_description}

Extract all relevant information and return in a structured format.
Include source text references where possible."""
        
        result = extractor.extract(text, prompt)
        
        if result.success:
            return json.dumps({
                "success": True,
                "extractions": result.extractions,
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result.error,
            }, indent=2)
            
    except Exception as e:
        return f"❌ Extraction failed: {e}"


async def extract_from_document(
    file_path: str,
    extraction_prompt: str,
    model: str = "gemini-2.5-flash",
    max_chunk_size: int = 3000,
) -> str:
    """
    Extract information from a document file.
    
    Args:
        file_path: Path to the document (txt, md, etc.)
        extraction_prompt: What to extract from the document
        model: LLM model to use
        max_chunk_size: Max characters per chunk for long documents
        
    Returns:
        JSON string of extracted information
    """
    from pathlib import Path
    
    try:
        from src.extraction.extractor import Extractor
    except ImportError:
        return (
            "❌ LangExtract not available. Install with:\n"
            "pip install langextract"
        )
    
    try:
        # Read document
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"❌ File not found: {file_path}"
        
        text = path.read_text(encoding="utf-8", errors="replace")
        
        extractor = Extractor(model_id=model)
        
        # Use multiple passes for long documents
        extraction_passes = 1 if len(text) < max_chunk_size else 3
        
        result = extractor.extract(
            text=text,
            prompt=extraction_prompt,
            extraction_passes=extraction_passes,
            max_char_buffer=max_chunk_size,
        )
        
        if result.success:
            return json.dumps({
                "success": True,
                "source_file": str(path),
                "document_length": len(text),
                "extraction_count": len(result.extractions),
                "extractions": result.extractions,
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result.error,
            }, indent=2)
            
    except Exception as e:
        return f"❌ Document extraction failed: {e}"


async def extract_key_value_pairs(
    text: str,
    fields: str,
    model: str = "gemini-2.5-flash",
) -> str:
    """
    Extract specific key-value pairs from text.
    
    Args:
        text: The text to extract from
        fields: Comma-separated field names to extract (e.g., "name, email, phone, address")
        model: LLM model to use
        
    Returns:
        JSON object with field names as keys
    """
    try:
        from src.extraction.extractor import Extractor
    except ImportError:
        return (
            "❌ LangExtract not available. Install with:\n"
            "pip install langextract"
        )
    
    try:
        extractor = Extractor(model_id=model)
        field_list = [f.strip() for f in fields.split(",")]
        
        prompt = f"""Extract the following fields from the text:
{chr(10).join(f'- {field}' for field in field_list)}

For each field found, extract the exact value as it appears in the text.
If a field is not found, indicate it as null."""
        
        result = extractor.extract(text, prompt)
        
        if result.success:
            # Convert extractions to key-value format
            extracted = {}
            for ext in result.extractions:
                ext_type = ext.get("type", "").lower()
                for field in field_list:
                    if field.lower() in ext_type or ext_type in field.lower():
                        extracted[field] = ext.get("text", "")
                        break
            
            return json.dumps({
                "success": True,
                "fields": extracted,
                "raw_extractions": result.extractions,
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result.error,
            }, indent=2)
            
    except Exception as e:
        return f"❌ Extraction failed: {e}"


def register_extraction_tools(registry: ToolRegistry) -> None:
    """Register extraction tools with the registry."""
    
    registry.register(
        name="extract_entities",
        description=(
            "Extract named entities (people, organizations, locations, etc.) from text "
            "using LangExtract with source grounding. Returns entities with their "
            "exact positions in the source text."
        ),
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to extract entities from",
                },
                "entity_types": {
                    "type": "string",
                    "description": "Comma-separated entity types to extract (e.g., 'person, organization, location, date')",
                },
                "model": {
                    "type": "string",
                    "description": "LLM model to use (default: gemini-2.5-flash)",
                    "default": "gemini-2.5-flash",
                },
            },
            "required": ["text", "entity_types"],
        },
        func=extract_entities_from_text,
    )
    
    registry.register(
        name="extract_structured",
        description=(
            "Extract structured information from text according to a schema description. "
            "Useful for parsing contracts, reports, emails, etc. into structured data."
        ),
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to extract from",
                },
                "schema_description": {
                    "type": "string",
                    "description": "Description of what to extract and expected structure",
                },
                "model": {
                    "type": "string",
                    "description": "LLM model to use",
                    "default": "gemini-2.5-flash",
                },
            },
            "required": ["text", "schema_description"],
        },
        func=extract_structured_info,
    )
    
    registry.register(
        name="extract_from_file",
        description=(
            "Extract information from a document file (txt, md, etc.). "
            "Handles long documents with chunking and multiple passes."
        ),
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the document file",
                },
                "extraction_prompt": {
                    "type": "string",
                    "description": "What information to extract from the document",
                },
                "model": {
                    "type": "string",
                    "description": "LLM model to use",
                    "default": "gemini-2.5-flash",
                },
            },
            "required": ["file_path", "extraction_prompt"],
        },
        func=extract_from_document,
    )
    
    registry.register(
        name="extract_fields",
        description=(
            "Extract specific fields/key-value pairs from text. "
            "Useful for parsing structured text like contact info, forms, receipts."
        ),
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to extract from",
                },
                "fields": {
                    "type": "string",
                    "description": "Comma-separated field names to extract (e.g., 'name, email, phone')",
                },
                "model": {
                    "type": "string",
                    "description": "LLM model to use",
                    "default": "gemini-2.5-flash",
                },
            },
            "required": ["text", "fields"],
        },
        func=extract_key_value_pairs,
    )
