#!/usr/bin/env python3
"""Test LangExtract integration."""

import asyncio
import json

# Sample text to extract from
SAMPLE_TEXT = """
Apple Inc. announced today that CEO Tim Cook will be visiting the new headquarters 
in Cupertino, California. The company reported quarterly revenue of $94.8 billion, 
beating analyst expectations. Meanwhile, Google's CEO Sundar Pichai commented on 
the AI industry trends during a conference in San Francisco. Microsoft's Satya Nadella 
also shared insights about cloud computing growth, with Azure revenue up 29% year-over-year.
Contact: press@apple.com, Phone: +1-408-996-1010
"""

async def test_entity_extraction():
    """Test basic entity extraction."""
    print("=" * 60)
    print("TEST 1: Entity Extraction")
    print("=" * 60)
    
    from src.tools.extraction import extract_entities_from_text
    
    result = await extract_entities_from_text(
        text=SAMPLE_TEXT,
        entity_types="person, organization, location, money",
        model="gpt-4o"  # Using OpenAI
    )
    
    print(result)
    print()

async def test_field_extraction():
    """Test key-value field extraction."""
    print("=" * 60)
    print("TEST 2: Field Extraction")
    print("=" * 60)
    
    from src.tools.extraction import extract_key_value_pairs
    
    result = await extract_key_value_pairs(
        text=SAMPLE_TEXT,
        fields="company_name, ceo_name, revenue, email, phone",
        model="gpt-4o"  # Using OpenAI
    )
    
    print(result)
    print()

async def test_structured_extraction():
    """Test schema-based structured extraction."""
    print("=" * 60)
    print("TEST 3: Structured Extraction")
    print("=" * 60)
    
    from src.tools.extraction import extract_structured_info
    
    schema = """
    Extract information about each company mentioned:
    - company_name: Name of the company
    - ceo: Name of the CEO
    - news: What news/update was mentioned
    - metrics: Any financial metrics mentioned
    """
    
    result = await extract_structured_info(
        text=SAMPLE_TEXT,
        schema_description=schema,
        model="gpt-4o"  # Using OpenAI
    )
    
    print(result)
    print()

async def test_direct_extractor():
    """Test the Extractor class directly."""
    print("=" * 60)
    print("TEST 4: Direct Extractor Class")
    print("=" * 60)
    
    from src.extraction.extractor import Extractor, ExtractionExample
    
    # Create extractor with OpenAI
    extractor = Extractor(model_id="gpt-4o")
    
    # Define a few-shot example
    examples = [
        ExtractionExample(
            text="John Smith is the CEO of Acme Corp in New York.",
            extractions=[
                {"type": "person", "text": "John Smith", "attributes": {"role": "CEO"}},
                {"type": "organization", "text": "Acme Corp"},
                {"type": "location", "text": "New York"},
            ]
        )
    ]
    
    # Extract with examples
    result = extractor.extract(
        text=SAMPLE_TEXT,
        prompt="Extract all people, organizations, and locations. Include roles/titles as attributes.",
        examples=examples,
    )
    
    if result.success:
        print(f"Found {len(result.extractions)} extractions:")
        for ext in result.extractions:
            print(f"  - [{ext['type']}] {ext['text']}")
            if ext.get('attributes'):
                print(f"    Attributes: {ext['attributes']}")
            if ext.get('source'):
                print(f"    Source position: {ext['source']}")
    else:
        print(f"Error: {result.error}")
    print()

async def main():
    print("\n🔬 LangExtract Integration Tests\n")
    
    # Check if Gemini API key is configured
    from src.config.settings import get_settings
    settings = get_settings()
    
    if not settings.providers.gemini.api_key:
        print("⚠️  No Gemini API key configured.")
        print("   Either:")
        print("   1. Set GOOGLE_API_KEY or LANGEXTRACT_API_KEY environment variable")
        print("   2. Add gemini.api_key to ~/.wingman/config.json")
        print("   3. Use OpenAI by changing model to 'gpt-4o' in the tests")
        print()
    
    try:
        await test_entity_extraction()
    except Exception as e:
        print(f"❌ Test 1 failed: {e}\n")
    
    try:
        await test_field_extraction()
    except Exception as e:
        print(f"❌ Test 2 failed: {e}\n")
    
    try:
        await test_structured_extraction()
    except Exception as e:
        print(f"❌ Test 3 failed: {e}\n")
    
    try:
        await test_direct_extractor()
    except Exception as e:
        print(f"❌ Test 4 failed: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
