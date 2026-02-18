"""
LangExtract Integration - Structured information extraction.

Uses Google's LangExtract library for extracting structured data
from unstructured text with source grounding and visualization.

Installation:
    pip install langextract
    # For OpenAI support:
    pip install langextract[openai]
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractionExample:
    """An example for few-shot prompting."""
    text: str
    extractions: list[dict[str, Any]]


@dataclass
class ExtractionSchema:
    """Schema definition for extraction tasks."""
    name: str
    description: str
    entity_types: list[str]
    attributes: dict[str, list[str]] = field(default_factory=dict)
    examples: list[ExtractionExample] = field(default_factory=list)

    def to_prompt(self) -> str:
        """Convert schema to extraction prompt."""
        prompt = f"{self.description}\n\n"
        prompt += f"Entity types to extract: {', '.join(self.entity_types)}\n"
        
        if self.attributes:
            prompt += "\nAttributes per entity type:\n"
            for entity_type, attrs in self.attributes.items():
                prompt += f"  - {entity_type}: {', '.join(attrs)}\n"
        
        return prompt


@dataclass
class ExtractionResult:
    """Result from an extraction operation."""
    success: bool
    extractions: list[dict[str, Any]] = field(default_factory=list)
    source_text: str = ""
    error: str | None = None
    visualization_html: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "extractions": self.extractions,
            "source_text": self.source_text[:500] if self.source_text else "",
            "error": self.error,
        }


class Extractor:
    """
    Structured information extractor using LangExtract.
    
    Provides:
    - Entity extraction with source grounding
    - Schema-based extraction with few-shot examples
    - Long document processing
    - Visualization generation
    """

    def __init__(
        self,
        model_id: str = "gemini-2.5-flash",
        api_key: str | None = None,
    ):
        self.model_id = model_id
        self.settings = get_settings()
        
        # Determine API key based on model
        if api_key:
            self.api_key = api_key
        elif "gemini" in model_id.lower():
            self.api_key = self.settings.providers.gemini.api_key
        elif "gpt" in model_id.lower() or "openai" in model_id.lower():
            self.api_key = self.settings.providers.openai.api_key
        else:
            self.api_key = None
        
        self._lx = None

    def _get_langextract(self):
        """Lazy import of langextract."""
        if self._lx is None:
            try:
                import langextract as lx
                self._lx = lx
            except ImportError:
                raise ImportError(
                    "langextract not installed. Run: pip install langextract\n"
                    "For OpenAI support: pip install langextract[openai]"
                )
        return self._lx

    def _create_default_example(self, prompt: str) -> ExtractionExample:
        """Create a default few-shot example based on the prompt."""
        return ExtractionExample(
            text="John Smith, CEO of Acme Corp, announced $50M revenue in New York. Contact: john@acme.com",
            extractions=[
                {"type": "person", "text": "John Smith", "attributes": {"role": "CEO"}},
                {"type": "organization", "text": "Acme Corp"},
                {"type": "money", "text": "$50M", "attributes": {"context": "revenue"}},
                {"type": "location", "text": "New York"},
                {"type": "email", "text": "john@acme.com"},
            ]
        )

    def extract(
        self,
        text: str,
        prompt: str,
        examples: list[ExtractionExample] | None = None,
        extraction_passes: int = 1,
        max_workers: int = 1,
        max_char_buffer: int = 3000,
    ) -> ExtractionResult:
        """
        Extract structured information from text.
        
        Args:
            text: The source text to extract from
            prompt: Extraction instructions
            examples: Optional few-shot examples (auto-generated if not provided)
            extraction_passes: Number of passes for recall
            max_workers: Parallel workers for long docs
            max_char_buffer: Chunk size for long documents
            
        Returns:
            ExtractionResult with extractions and metadata
        """
        lx = self._get_langextract()
        
        # LangExtract requires examples - create default if not provided
        if not examples:
            examples = [self._create_default_example(prompt)]
        
        # Convert examples to LangExtract format
        lx_examples = []
        for ex in examples:
            lx_extractions = []
            for ext in ex.extractions:
                lx_extractions.append(lx.data.Extraction(
                    extraction_class=ext.get("type", "entity"),
                    extraction_text=ext.get("text", ""),
                    attributes=ext.get("attributes", {}),
                ))
            lx_examples.append(lx.data.ExampleData(
                text=ex.text,
                extractions=lx_extractions,
            ))
        
        # Determine model settings
        use_openai = "gpt" in self.model_id.lower() or "openai" in self.model_id.lower()
        
        try:
            # Run extraction with appropriate settings
            extract_kwargs = {
                "text_or_documents": text,
                "prompt_description": prompt,
                "examples": lx_examples,
                "model_id": self.model_id,
                "api_key": self.api_key,
                "extraction_passes": extraction_passes,
                "max_workers": max_workers,
                "max_char_buffer": max_char_buffer,
            }
            
            # OpenAI models need different settings
            if use_openai:
                extract_kwargs["fence_output"] = True
                extract_kwargs["use_schema_constraints"] = False
            
            result = lx.extract(**extract_kwargs)
            
            # Convert results
            extractions = []
            for ext in result.extractions:
                extraction_dict = {
                    "type": ext.extraction_class,
                    "text": ext.extraction_text,
                    "attributes": ext.attributes if hasattr(ext, 'attributes') else {},
                }
                
                # Add source grounding if available
                if hasattr(ext, 'char_interval') and ext.char_interval:
                    extraction_dict["source"] = {
                        "start": ext.char_interval.start_pos,
                        "end": ext.char_interval.end_pos,
                    }
                
                extractions.append(extraction_dict)
            
            return ExtractionResult(
                success=True,
                extractions=extractions,
                source_text=text,
            )
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractionResult(
                success=False,
                error=str(e),
                source_text=text,
            )

    def extract_with_schema(
        self,
        text: str,
        schema: ExtractionSchema,
        **kwargs,
    ) -> ExtractionResult:
        """Extract using a predefined schema."""
        prompt = schema.to_prompt()
        examples = schema.examples if schema.examples else None
        return self.extract(text, prompt, examples, **kwargs)

    def visualize(
        self,
        result: ExtractionResult,
        output_path: Path | str | None = None,
    ) -> str:
        """
        Generate interactive HTML visualization.
        
        Args:
            result: Extraction result to visualize
            output_path: Optional path to save HTML file
            
        Returns:
            HTML content as string
        """
        lx = self._get_langextract()
        
        try:
            # Create a temporary JSONL for visualization
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                doc_data = {
                    "text": result.source_text,
                    "extractions": result.extractions,
                }
                f.write(json.dumps(doc_data) + "\n")
                temp_path = f.name
            
            # Generate visualization
            html_content = lx.visualize(temp_path)
            
            # Clean up
            Path(temp_path).unlink()
            
            # Save if path provided
            if output_path:
                Path(output_path).write_text(html_content)
            
            result.visualization_html = html_content
            return html_content
            
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            return f"<html><body>Visualization error: {e}</body></html>"


# Convenience functions

async def extract_entities(
    text: str,
    entity_types: list[str],
    model_id: str = "gemini-2.5-flash",
) -> list[dict[str, Any]]:
    """
    Quick entity extraction.
    
    Args:
        text: Source text
        entity_types: Types of entities to extract (e.g., ["person", "organization"])
        model_id: LLM model to use
        
    Returns:
        List of extracted entities
    """
    extractor = Extractor(model_id=model_id)
    prompt = f"Extract all {', '.join(entity_types)} from the text."
    result = extractor.extract(text, prompt)
    return result.extractions if result.success else []


async def extract_structured_data(
    text: str,
    schema: dict[str, Any],
    model_id: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    """
    Extract data according to a JSON schema.
    
    Args:
        text: Source text
        schema: JSON schema defining expected structure
        model_id: LLM model to use
        
    Returns:
        Extracted data matching schema
    """
    extractor = Extractor(model_id=model_id)
    
    prompt = f"""Extract information from the text according to this schema:
{json.dumps(schema, indent=2)}

Return the extracted data as JSON."""
    
    result = extractor.extract(text, prompt)
    
    if result.success and result.extractions:
        # Try to parse as structured data
        return {"extractions": result.extractions}
    
    return {"error": result.error or "No extractions found"}
