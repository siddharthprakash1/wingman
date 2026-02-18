"""
Text Chunker - Split documents into smaller chunks for embedding.

Supports multiple chunking strategies:
- Fixed size with overlap
- Sentence-based
- Paragraph-based
- Semantic (using embeddings)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Chunk:
    """A chunk of text with metadata."""
    text: str
    index: int
    start_char: int
    end_char: int
    metadata: dict = field(default_factory=dict)
    
    @property
    def char_count(self) -> int:
        return len(self.text)


class TextChunker:
    """Split text into chunks for embedding."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: Literal["fixed", "sentence", "paragraph"] = "sentence",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
    
    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """Split text into chunks."""
        if not text.strip():
            return []
        
        if self.strategy == "fixed":
            return self._chunk_fixed(text, metadata)
        elif self.strategy == "sentence":
            return self._chunk_sentence(text, metadata)
        elif self.strategy == "paragraph":
            return self._chunk_paragraph(text, metadata)
        else:
            return self._chunk_fixed(text, metadata)
    
    def _chunk_fixed(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """Fixed-size chunking with overlap."""
        chunks = []
        start = 0
        index = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Try to end at a word boundary
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    index=index,
                    start_char=start,
                    end_char=end,
                    metadata=metadata or {},
                ))
                index += 1
            
            # Move start with overlap
            start = end - self.chunk_overlap
            if start >= end:
                start = end
        
        return chunks
    
    def _chunk_sentence(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """Sentence-based chunking."""
        # Split into sentences
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_start = 0
        index = 0
        char_pos = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_len = len(sentence)
            
            # If single sentence exceeds chunk size, use fixed chunking for it
            if sentence_len > self.chunk_size:
                # Flush current chunk
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(Chunk(
                        text=chunk_text,
                        index=index,
                        start_char=chunk_start,
                        end_char=char_pos,
                        metadata=metadata or {},
                    ))
                    index += 1
                    current_chunk = []
                    current_length = 0
                
                # Chunk the long sentence
                sub_chunks = self._chunk_fixed(sentence, metadata)
                for sc in sub_chunks:
                    sc.index = index
                    sc.start_char += char_pos
                    sc.end_char += char_pos
                    chunks.append(sc)
                    index += 1
                
                char_pos += sentence_len + 1
                chunk_start = char_pos
                continue
            
            # Check if adding this sentence exceeds chunk size
            if current_length + sentence_len + 1 > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    index=index,
                    start_char=chunk_start,
                    end_char=char_pos,
                    metadata=metadata or {},
                ))
                index += 1
                
                # Keep overlap sentences
                overlap_text = chunk_text[-self.chunk_overlap:] if len(chunk_text) > self.chunk_overlap else ""
                if overlap_text:
                    # Find sentence boundary in overlap
                    overlap_sentences = re.split(sentence_pattern, overlap_text)
                    current_chunk = [s.strip() for s in overlap_sentences if s.strip()]
                    current_length = sum(len(s) for s in current_chunk)
                else:
                    current_chunk = []
                    current_length = 0
                
                chunk_start = char_pos
            
            current_chunk.append(sentence)
            current_length += sentence_len + 1
            char_pos += sentence_len + 1
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                index=index,
                start_char=chunk_start,
                end_char=char_pos,
                metadata=metadata or {},
            ))
        
        return chunks
    
    def _chunk_paragraph(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """Paragraph-based chunking."""
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_start = 0
        index = 0
        char_pos = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_len = len(para)
            
            # If single paragraph exceeds chunk size, use sentence chunking
            if para_len > self.chunk_size:
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(Chunk(
                        text=chunk_text,
                        index=index,
                        start_char=chunk_start,
                        end_char=char_pos,
                        metadata=metadata or {},
                    ))
                    index += 1
                    current_chunk = []
                    current_length = 0
                
                # Use sentence chunking for long paragraph
                sub_chunks = self._chunk_sentence(para, metadata)
                for sc in sub_chunks:
                    sc.index = index
                    sc.start_char += char_pos
                    sc.end_char += char_pos
                    chunks.append(sc)
                    index += 1
                
                char_pos += para_len + 2
                chunk_start = char_pos
                continue
            
            if current_length + para_len + 2 > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(Chunk(
                    text=chunk_text,
                    index=index,
                    start_char=chunk_start,
                    end_char=char_pos,
                    metadata=metadata or {},
                ))
                index += 1
                current_chunk = []
                current_length = 0
                chunk_start = char_pos
            
            current_chunk.append(para)
            current_length += para_len + 2
            char_pos += para_len + 2
        
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                index=index,
                start_char=chunk_start,
                end_char=char_pos,
                metadata=metadata or {},
            ))
        
        return chunks


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    strategy: str = "sentence",
) -> list[Chunk]:
    """Convenience function to chunk text."""
    chunker = TextChunker(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        strategy=strategy,
    )
    return chunker.chunk(text)
