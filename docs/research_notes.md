# LangExtract Library Research Notes

## Overview

**LangExtract** is an open-source Python library developed by Google for extracting structured information from unstructured text using Large Language Models (LLMs). It provides precise source grounding, schema-based extraction, and interactive visualization capabilities.

- **GitHub Repository**: https://github.com/google/langextract
- **PyPI Package**: https://pypi.org/project/langextract/
- **Official Documentation**: https://developers.google.com/health-ai-developer-foundations/libraries/langextract
- **Latest Version**: 1.1.1 (as of Nov 27, 2025)
- **License**: Apache-2.0
- **Python Requirements**: Python >= 3.10

---

## Core Capabilities

### 1. Structured Data Extraction
- Extracts structured information from unstructured text based on user-defined instructions
- Uses few-shot prompting with examples to guide the LLM
- Enforces consistent output schemas using controlled generation (for supported models like Gemini)

### 2. Schema-Based Extraction
- Define extraction tasks using prompts and examples
- No model fine-tuning required - works with few-shot examples
- Supports custom entity types and attributes
- Schema enforcement through controlled generation (Gemini models)

### 3. Source Grounding
- Maps every extraction to exact character offsets in source text
- Enables visual highlighting for traceability and verification
- Provides `char_interval` with `start_pos` and `end_pos` for each extraction

### 4. Long Document Processing
- Optimized for long documents using:
  - Text chunking strategy
  - Parallel processing (`max_workers` parameter)
  - Multiple extraction passes (`extraction_passes` parameter)
- Overcomes "needle-in-a-haystack" challenges in large contexts

### 5. Interactive Visualization
- Generates self-contained interactive HTML files
- Visualizes extracted entities in original context
- Supports thousands of annotations
- Works in Jupyter/Colab or as standalone HTML

---

## LLM Integration

### Supported Model Providers

| Provider | Model ID Example | Requirements |
|----------|-----------------|--------------|
| **Google Gemini** (default) | `gemini-2.5-flash`, `gemini-2.5-pro` | `LANGEXTRACT_API_KEY` or `GOOGLE_API_KEY` |
| **Google Vertex AI** | `gemini-2.5-flash` | Service account auth, project ID |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini` | `OPENAI_API_KEY`, `pip install langextract[openai]` |
| **Ollama (Local)** | `gemma2:2b` | Ollama server running locally |
| **Custom Providers** | Any | Plugin system available |

### Model Recommendations
- **Default**: `gemini-2.5-flash` - best balance of speed, cost, and quality
- **Complex tasks**: `gemini-2.5-pro` - deeper reasoning capabilities
- **Production**: Tier 2 Gemini quota recommended for throughput

---

## Key Classes and Data Structures

### Core Classes

#### `lx.data.ExampleData`
Represents a training example for few-shot prompting.
```python
ExampleData(
    text="sample text to extract from",
    extractions=[Extraction(...), ...]
)
```

#### `lx.data.Extraction`
Represents a single extracted entity.
```python
Extraction(
    extraction_class="entity_type",      # Category/type of extraction
    extraction_text="exact text",        # Verbatim text from source
    attributes={"key": "value"},         # Additional context/metadata
    char_interval=CharInterval(...)      # Source location (auto-populated)
)
```

#### `lx.data.CharInterval`
Represents character offsets for source grounding.
```python
CharInterval(
    start_pos=0,    # Start character position
    end_pos=10      # End character position
)
```

### Main Function

#### `lx.extract()`
Primary extraction function.
```python
result = lx.extract(
    text_or_documents=input_text,       # Text, URL, or list of documents
    prompt_description=prompt,          # Extraction instructions
    examples=examples,                  # List of ExampleData objects
    model_id="gemini-2.5-flash",        # Model identifier
    api_key=None,                       # Optional API key
    extraction_passes=1,                # Number of extraction passes
    max_workers=1,                      # Parallel workers
    max_char_buffer=3000,               # Chunk size for long docs
    language_model_params={},           # Provider-specific params
    fence_output=False,                 # For non-Gemini models
    use_schema_constraints=True         # Schema enforcement (Gemini only)
)
```

### I/O Functions

#### `lx.io.save_annotated_documents()`
Save extraction results to JSONL format.
```python
lx.io.save_annotated_documents(
    [result],
    output_name="results.jsonl",
    output_dir="."
)
```

#### `lx.visualize()`
Generate interactive HTML visualization.
```python
html_content = lx.visualize("results.jsonl")
```

---

## Dependencies

### Core Dependencies (installed with `pip install langextract`)
- Modern Python packaging with `pyproject.toml`
- Google Generative AI client libraries (for Gemini)

### Optional Dependencies
```bash
# OpenAI support
pip install langextract[openai]

# Development tools
pip install langextract[dev]

# Testing
pip install langextract[test]

# Jupyter/Notebook support
pip install langextract[notebook]

# All extras
pip install langextract[all]
```

---

## Authentication Requirements

### Environment Variables

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `LANGEXTRACT_API_KEY` | Primary API key | Gemini (AI Studio) |
| `GOOGLE_API_KEY` | Alternative Google key | Gemini |
| `OPENAI_API_KEY` | OpenAI access | OpenAI models |
| `ANTHROPIC_API_KEY` | Anthropic access | Claude models |

### Authentication Methods

1. **Environment Variable** (Recommended for production)
   ```bash
   export LANGEXTRACT_API_KEY="your-api-key"
   ```

2. **.env File** (Recommended for development)
   ```bash
   # .env file
   LANGEXTRACT_API_KEY=your-api-key-here
   ```

3. **Direct in Code** (Not recommended for production)
   ```python
   result = lx.extract(..., api_key="your-api-key")
   ```

4. **Vertex AI Service Account**
   ```python
   result = lx.extract(
       ...,
       language_model_params={
           "vertexai": True,
           "project": "your-project-id",
           "location": "global"
       }
   )
   ```

5. **Ollama (No API Key)**
   ```python
   result = lx.extract(
       ...,
       model_id="gemma2:2b",
       model_url="http://localhost:11434",
       fence_output=False,
       use_schema_constraints=False
   )
   ```

---

## Supported Output Formats

### 1. JSONL (JSON Lines)
- Primary output format for extraction results
- Each line contains one document's extraction data
- Processable line-by-line for large datasets

### 2. Interactive HTML
- Self-contained visualization files
- Color-coded entity highlighting
- Click-through navigation
- Attribute inspection

### 3. Python Objects
- `AnnotatedDocument` objects with `extractions` property
- Each extraction contains:
  - `extraction_class`: Entity type
  - `extraction_text`: Verbatim extracted text
  - `attributes`: Dictionary of additional metadata
  - `char_interval`: Source location (`start_pos`, `end_pos`)

### 4. Pydantic Integration
- Schema validation through controlled generation
- Type-safe extraction outputs (Gemini models)

---

## Best Practices

### Few-Shot Prompting
- Provide 1-3 high-quality examples
- Use exact verbatim text in `extraction_text` (no paraphrasing)
- List extractions in order of appearance
- Include meaningful attributes for context

### Long Document Processing
```python
# For detailed extraction
result = lx.extract(
    ...,
    extraction_passes=3,        # Multiple passes for recall
    max_workers=20,             # Parallel processing
    max_char_buffer=1000        # Smaller chunks for accuracy
)
```

### Production Settings
```python
# For speed
result = lx.extract(
    ...,
    extraction_passes=1,
    max_char_buffer=3000,
    max_workers=30
)

# For accuracy
result = lx.extract(
    ...,
    extraction_passes=5,
    max_char_buffer=800,
    max_workers=10
)
```

---

## Use Cases

1. **Healthcare/Medical**
   - Medication extraction from clinical notes
   - Radiology report structuring (RadExtract)
   - Entity relationship extraction

2. **Legal**
   - Contract clause extraction
   - Legal entity identification

3. **Finance**
   - Financial metric extraction
   - Entity relationship mapping

4. **Customer Support**
   - Ticket categorization
   - Urgency detection
   - Product issue extraction

5. **HR/Recruiting**
   - Resume parsing
   - Employee information extraction

---

## Limitations and Considerations

1. **Not an officially supported Google product** (subject to Apache 2.0 License)
2. **Health AI Developer Foundations Terms of Use** apply for health-related applications
3. **OpenAI models** require `fence_output=True` and `use_schema_constraints=False`
4. **Local models** (Ollama) may have lower accuracy than cloud models
5. **API costs** apply for cloud-based LLM usage
6. **Rate limits** may apply depending on quota tier

---

## Additional Resources

- **GitHub Examples**: https://github.com/google/langextract/tree/main/examples
- **RadExtract Demo**: https://google-radextract.hf.space
- **Romeo & Juliet Example**: Full novel extraction demonstration
- **Medication Extraction Example**: Healthcare use case
- **Community Providers**: Extensible plugin system for custom models

---

## Research Summary

LangExtract provides a powerful, flexible framework for structured information extraction from unstructured text. Its key differentiators are:

1. **Source Grounding**: Every extraction mapped to exact source location
2. **Schema Enforcement**: Controlled generation for reliable structured outputs
3. **Few-Shot Learning**: No fine-tuning required, works with examples
4. **Multi-Provider Support**: Gemini, OpenAI, Ollama, and custom providers
5. **Production Ready**: Chunking, parallelization, and multiple extraction passes
6. **Visualization**: Interactive HTML output for verification and review

The library is particularly well-suited for domain-specific extraction tasks where traditional NLP libraries (spaCy, NLTK) fall short due to lack of context understanding or need for custom entity types.
