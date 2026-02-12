# LangExtract Library Research Notes

## Overview

**LangExtract** is an open-source Python library developed by Google for extracting structured information from unstructured text documents using Large Language Models (LLMs). It provides precise source grounding, reliable structured outputs, and interactive visualization capabilities.

- **GitHub Repository**: https://github.com/google/langextract
- **PyPI Package**: https://pypi.org/project/langextract/
- **Current Version**: 1.1.1 (as of November 27, 2025)
- **License**: Apache-2.0
- **Python Requirements**: Python >= 3.10

---

## Core Capabilities

### 1. Structured Data Extraction
- Extracts structured information from unstructured text based on user-defined instructions
- Uses few-shot examples to guide the extraction process
- Supports domain-specific extraction without model fine-tuning

### 2. Schema-Based Extraction
- Enforces consistent output schemas based on few-shot examples
- Leverages "Controlled Generation" in supported models (Gemini) for structured outputs
- Supports both JSON and YAML output formats

### 3. Source Grounding
- Maps every extraction to its exact character offsets in the source text
- Enables visual highlighting for traceability and verification
- Supports fuzzy matching and alignment status tracking

### 4. Long Document Processing
- Optimized for long documents using text chunking strategy
- Parallel processing with configurable workers
- Multiple extraction passes for improved recall
- Context window management for cross-chunk coreference resolution

### 5. Interactive Visualization
- Generates self-contained interactive HTML files
- Visualizes extracted entities in their original context
- Supports thousands of annotations
- Works in Jupyter/Colab environments

---

## Key Classes and Components

### Core Data Classes (`langextract.core.data`)

#### `Extraction`
Represents an extracted entity from text.

```python
@dataclasses.dataclass
class Extraction:
    extraction_class: str          # Class/category of extraction
    extraction_text: str           # The extracted text
    char_interval: CharInterval    # Position in source text
    alignment_status: AlignmentStatus  # Match quality
    extraction_index: int          # Order in extraction list
    group_index: int               # Grouping index
    description: str               # Description of extraction
    attributes: dict               # Additional attributes
```

#### `Document`
Represents input text/document for processing.

```python
@dataclasses.dataclass
class Document:
    text: str                      # Raw text content
    document_id: str               # Unique identifier (auto-generated)
    additional_context: str        # Context for prompt instructions
    tokenized_text: TokenizedText  # Computed tokenization
```

#### `AnnotatedDocument`
Represents a document with extracted information.

```python
@dataclasses.dataclass
class AnnotatedDocument:
    document_id: str
    extractions: list[Extraction]
    text: str
```

#### `ExampleData`
Provides few-shot examples for guiding extraction.

```python
@dataclasses.dataclass
class ExampleData:
    text: str                      # Input text example
    extractions: list[Extraction]  # Expected extractions
```

#### `CharInterval`
Represents character position in source text.

```python
@dataclasses.dataclass
class CharInterval:
    start_pos: int | None          # Start position (inclusive)
    end_pos: int | None            # End position (exclusive)
```

### Main API Functions

#### `extract()`
Primary extraction function.

```python
lx.extract(
    text_or_documents: str | Iterable[Document],
    prompt_description: str,           # Instructions for extraction
    examples: Sequence[ExampleData],    # Few-shot examples
    model_id: str = "gemini-2.5-flash", # Model to use
    api_key: str | None = None,         # API key (or env var)
    max_char_buffer: int = 1000,        # Chunk size
    extraction_passes: int = 1,         # Number of passes
    max_workers: int = 10,              # Parallel workers
    temperature: float | None = None,   # Sampling temperature
    use_schema_constraints: bool = True, # Structured output
    fence_output: bool | None = None,   # Markdown fencing
    # ... additional parameters
) -> AnnotatedDocument | list[AnnotatedDocument]
```

#### `visualize()`
Generates interactive HTML visualization.

```python
lx.visualize(
    jsonl_path: str  # Path to JSONL file with extraction results
) -> str | HTML    # HTML content
```

### Provider System

LangExtract uses a provider-based architecture for LLM support:

#### Built-in Providers

1. **Gemini Provider** (`langextract.providers.gemini.GeminiLanguageModel`)
   - Default provider for Google Gemini models
   - Supports both AI Studio API and Vertex AI
   - Supports structured output with schema constraints
   - Supports batch processing via Vertex AI Batch API

2. **OpenAI Provider** (`langextract.providers.openai.OpenAILanguageModel`)
   - Supports GPT models (gpt-4o, etc.)
   - Requires `pip install langextract[openai]`
   - Requires `fence_output=True` and `use_schema_constraints=False`

3. **Ollama Provider** (`langextract.providers.ollama.OllamaLanguageModel`)
   - Supports local LLMs via Ollama
   - No API key required
   - Default URL: http://localhost:11434

#### Provider Registration
Providers are registered via entry points in `pyproject.toml`:
```toml
[project.entry-points."langextract.providers"]
gemini = "langextract.providers.gemini:GeminiLanguageModel"
ollama = "langextract.providers.ollama:OllamaLanguageModel"
openai = "langextract.providers.openai:OpenAILanguageModel"
```

### Factory and Configuration

#### `ModelConfig`
Configuration for model instantiation.

```python
@dataclasses.dataclass
class ModelConfig:
    model_id: str | None = None
    provider: str | None = None
    provider_kwargs: dict = field(default_factory=dict)
```

#### `create_model()`
Factory function for creating model instances.

```python
from langextract.factory import create_model, ModelConfig

model = create_model(ModelConfig(
    model_id="gemini-2.5-flash",
    provider_kwargs={"api_key": "..."}
))
```

---

## Dependencies

### Core Dependencies (from pyproject.toml)
```
absl-py>=1.0.0
aiohttp>=3.8.0
async_timeout>=4.0.0
exceptiongroup>=1.1.0
google-genai>=1.39.0          # Gemini API client
google-cloud-storage>=2.14.0
ml-collections>=0.1.0
more-itertools>=8.0.0
numpy>=1.20.0
pandas>=1.3.0
pydantic>=1.8.0               # Data validation
python-dotenv>=0.19.0         # Environment variables
PyYAML>=6.0
regex>=2023.0.0
requests>=2.25.0
tqdm>=4.64.0                  # Progress bars
typing-extensions>=4.0.0
```

### Optional Dependencies
- **openai**: `openai>=1.50.0` (for OpenAI models)
- **dev**: pyink, isort, pylint, pytype, tox, pre-commit
- **test**: pytest, tomli
- **notebook**: ipython, notebook

---

## Authentication Requirements

### API Keys

#### Gemini Models
- Source: [Google AI Studio](https://aistudio.google.com/) or [Vertex AI](https://cloud.google.com/vertex-ai)
- Environment Variable: `LANGEXTRACT_API_KEY` or `GEMINI_API_KEY`
- Direct parameter: `api_key="..."` (not recommended for production)

#### OpenAI Models
- Source: [OpenAI Platform](https://platform.openai.com/)
- Environment Variable: `OPENAI_API_KEY` or `LANGEXTRACT_API_KEY`

#### Vertex AI (Enterprise)
- Uses service account credentials
- Requires: `project`, `location`, `vertexai=True`
- No API key needed when using service accounts

### Environment Configuration

Recommended approach using `.env` file:
```bash
# .env file
LANGEXTRACT_API_KEY=your-api-key-here
```

Or environment variable:
```bash
export LANGEXTRACT_API_KEY="your-api-key-here"
```

---

## Supported Output Formats

### JSON (Default)
- Primary format for structured extraction
- Required for schema constraints with Gemini
- Output saved as `.jsonl` files

### YAML
- Alternative format supported
- Not compatible with Gemini schema constraints

### Format Selection
```python
lx.extract(
    ...,
    format_type=lx.data.FormatType.JSON  # or FormatType.YAML
)
```

---

## Model Support

### Recommended Models

| Model | Provider | Use Case |
|-------|----------|----------|
| gemini-2.5-flash | Gemini | Default, balanced speed/cost/quality |
| gemini-2.5-pro | Gemini | Complex tasks requiring reasoning |
| gpt-4o | OpenAI | Alternative cloud model |
| gemma2:2b | Ollama | Local inference, no API key |

### Model Selection
```python
# Gemini (default)
result = lx.extract(..., model_id="gemini-2.5-flash")

# OpenAI
result = lx.extract(..., model_id="gpt-4o")

# Ollama (local)
result = lx.extract(..., model_id="gemma2:2b", model_url="http://localhost:11434")
```

---

## Advanced Features

### Batch Processing (Vertex AI)
```python
result = lx.extract(
    ...,
    language_model_params={
        "vertexai": True,
        "batch": {"enabled": True}
    }
)
```

### Multiple Extraction Passes
```python
result = lx.extract(
    ...,
    extraction_passes=3,  # Improves recall
    max_workers=20        # Parallel processing
)
```

### Custom Tokenizer
```python
from langextract.core.tokenizer import RegexTokenizer

tokenizer = RegexTokenizer()
result = lx.extract(..., tokenizer=tokenizer)
```

### Prompt Validation
```python
from langextract import prompt_validation as pv

result = lx.extract(
    ...,
    prompt_validation_level=pv.PromptValidationLevel.WARNING,  # or .OFF, .ERROR
    prompt_validation_strict=False
)
```

---

## Installation

### From PyPI (Recommended)
```bash
pip install langextract
```

### With OpenAI Support
```bash
pip install langextract[openai]
```

### Development Installation
```bash
git clone https://github.com/google/langextract.git
cd langextract
pip install -e ".[dev,test]"
```

### Docker
```bash
docker build -t langextract .
docker run --rm -e LANGEXTRACT_API_KEY="your-api-key" langextract python your_script.py
```

---

## Usage Example

```python
import langextract as lx
import textwrap

# 1. Define extraction instructions
prompt = textwrap.dedent("""\
    Extract characters, emotions, and relationships in order of appearance.
    Use exact text for extractions. Do not paraphrase or overlap entities.
    Provide meaningful attributes for each entity to add context.""")

# 2. Provide few-shot examples
examples = [
    lx.data.ExampleData(
        text="ROMEO. But soft! What light through yonder window breaks?",
        extractions=[
            lx.data.Extraction(
                extraction_class="character",
                extraction_text="ROMEO",
                attributes={"emotional_state": "wonder"}
            ),
        ]
    )
]

# 3. Run extraction
input_text = "Lady Juliet gazed longingly at the stars..."
result = lx.extract(
    text_or_documents=input_text,
    prompt_description=prompt,
    examples=examples,
    model_id="gemini-2.5-flash"
)

# 4. Save and visualize
lx.io.save_annotated_documents([result], output_name="results.jsonl")
html = lx.visualize("results.jsonl")
```

---

## References

1. **Official Documentation**: https://github.com/google/langextract/blob/main/README.md
2. **PyPI Package**: https://pypi.org/project/langextract/
3. **Google Developer Blog**: https://developers.googleblog.com/en/introducing-langextract-a-gemini-powered-information-extraction-library/
4. **Research Paper**: https://doi.org/10.5281/zenodo.17015089
5. **RadExtract Demo**: https://google-radextract.hf.space

---

## Notes

- This is **not an officially supported Google product**
- For health-related applications, subject to Health AI Developer Foundations Terms of Use
- Gemini models have lifecycle with defined retirement dates - check model version documentation
- Examples drive model behavior - ensure extraction_text is verbatim from example text
- Each extraction_pass reprocesses tokens, increasing API costs
