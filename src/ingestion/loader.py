"""
Document Loader - Load various file formats.

Supports: PDF, TXT, MD, HTML, JSON, CSV
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A loaded document with content and metadata."""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    pages: list[str] = field(default_factory=list)
    
    @property
    def num_pages(self) -> int:
        return len(self.pages) if self.pages else 1
    
    @property
    def char_count(self) -> int:
        return len(self.content)


class DocumentLoader:
    """Load documents from various file formats."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.md', '.html', '.htm', '.json', '.csv'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit
    
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path).expanduser().resolve()
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        # Check file size
        file_size = self.file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file_size / (1024*1024):.1f}MB. "
                f"Maximum allowed: {self.MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )
        
        if file_size == 0:
            raise ValueError(f"File is empty: {self.file_path}")
        
        self.file_type = self.file_path.suffix.lower()
        if self.file_type not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {self.file_type}. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )
    
    def load(self) -> Document:
        """Load the document and return content with metadata."""
        logger.info(f"Loading {self.file_type} file: {self.file_path}")
        
        loaders = {
            '.pdf': self._load_pdf,
            '.txt': self._load_text,
            '.md': self._load_text,
            '.html': self._load_html,
            '.htm': self._load_html,
            '.json': self._load_json,
            '.csv': self._load_csv,
        }
        
        loader = loaders.get(self.file_type)
        if not loader:
            raise ValueError(f"No loader for: {self.file_type}")
        
        return loader()
    
    def _load_pdf(self) -> Document:
        """Load PDF using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
        
        doc = fitz.open(self.file_path)
        pages = []
        full_text = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            pages.append(text)
            full_text.append(text)
        
        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "page_count": len(doc),
            "file_size": self.file_path.stat().st_size,
        }
        
        doc.close()
        
        return Document(
            content="\n\n".join(full_text),
            metadata=metadata,
            source=str(self.file_path),
            pages=pages,
        )
    
    def _load_text(self) -> Document:
        """Load plain text or markdown."""
        content = self.file_path.read_text(encoding='utf-8', errors='replace')
        
        return Document(
            content=content,
            metadata={
                "file_size": self.file_path.stat().st_size,
                "encoding": "utf-8",
            },
            source=str(self.file_path),
        )
    
    def _load_html(self) -> Document:
        """Load HTML and extract text."""
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self.skip_tags = {'script', 'style', 'meta', 'link'}
                self.current_tag = None
            
            def handle_starttag(self, tag, attrs):
                self.current_tag = tag
            
            def handle_data(self, data):
                if self.current_tag not in self.skip_tags:
                    text = data.strip()
                    if text:
                        self.text_parts.append(text)
        
        html_content = self.file_path.read_text(encoding='utf-8', errors='replace')
        extractor = TextExtractor()
        extractor.feed(html_content)
        
        return Document(
            content="\n".join(extractor.text_parts),
            metadata={
                "file_size": self.file_path.stat().st_size,
                "format": "html",
            },
            source=str(self.file_path),
        )
    
    def _load_json(self) -> Document:
        """Load JSON and convert to readable text."""
        data = json.loads(self.file_path.read_text(encoding='utf-8'))
        content = json.dumps(data, indent=2, ensure_ascii=False)
        
        return Document(
            content=content,
            metadata={
                "file_size": self.file_path.stat().st_size,
                "format": "json",
                "keys": list(data.keys()) if isinstance(data, dict) else None,
            },
            source=str(self.file_path),
        )
    
    def _load_csv(self) -> Document:
        """Load CSV and convert to readable text."""
        import csv
        
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if not rows:
            return Document(content="", source=str(self.file_path))
        
        headers = rows[0] if rows else []
        content_lines = []
        
        for i, row in enumerate(rows[1:], 1):
            row_text = ", ".join(
                f"{headers[j]}: {val}" if j < len(headers) else val
                for j, val in enumerate(row)
            )
            content_lines.append(f"Row {i}: {row_text}")
        
        return Document(
            content="\n".join(content_lines),
            metadata={
                "file_size": self.file_path.stat().st_size,
                "format": "csv",
                "headers": headers,
                "row_count": len(rows) - 1,
            },
            source=str(self.file_path),
        )


def load_document(file_path: str | Path) -> Document:
    """Convenience function to load a document."""
    loader = DocumentLoader(file_path)
    return loader.load()
