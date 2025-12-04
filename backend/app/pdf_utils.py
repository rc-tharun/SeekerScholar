"""
PDF and document text extraction utilities.
Handles PDF, DOCX, and TXT file extraction efficiently.
"""
import os
import re
import tempfile
from typing import Optional
from pathlib import Path

from pypdf import PdfReader
from docx import Document

from app.config import Config


def extract_abstract_from_text(text: str) -> Optional[str]:
    """
    Try to extract abstract section from text.
    
    Args:
        text: Full text content
        
    Returns:
        Abstract text if found, None otherwise
    """
    abstract_patterns = [
        r"(?i)abstract\s*:?\s*(.+?)(?=\n\s*(?:introduction|1\.|keywords|references))",
        r"(?i)abstract\s*:?\s*(.+?)(?=\n\n)",
    ]
    
    for pattern in abstract_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            abstract_text = match.group(1).strip()
            if len(abstract_text) > 50:  # Ensure it's substantial
                return abstract_text
    
    return None


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to max_length, trying to break at word boundary.
    
    Args:
        text: Text to truncate
        max_length: Maximum length in characters
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    # If we can break at a reasonable word boundary (within 80% of max)
    if last_space > max_length * 0.8:
        return truncated[:last_space]
    
    return truncated


def first_n_words(text: str, n: int = 100) -> str:
    """
    Return the first n words of the given text.
    Words are separated by whitespace. Collapses multiple spaces/newlines.
    
    Args:
        text: Input text
        n: Number of words to return (default: 100)
        
    Returns:
        First n words as a single string
    """
    if not text:
        return ""
    
    # Normalize whitespace and split into words
    tokens = text.split()
    
    if len(tokens) <= n:
        return " ".join(tokens)
    
    return " ".join(tokens[:n])


async def extract_text_from_pdf(file_path: str, max_length: int) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to PDF file
        max_length: Maximum length of extracted text
        
    Returns:
        Extracted text (truncated if needed)
    """
    text_chunks = []
    reader = PdfReader(file_path)
    
    for page in reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
        except Exception:
            continue
    
    full_text = "\n".join(text_chunks)
    
    # Try to extract abstract first
    abstract = extract_abstract_from_text(full_text)
    if abstract:
        return truncate_text(abstract, max_length)
    
    # Otherwise return truncated full text
    return truncate_text(full_text, max_length)


def extract_text_from_docx(file_path: str, max_length: int) -> str:
    """
    Extract text from DOCX file.
    
    Args:
        file_path: Path to DOCX file
        max_length: Maximum length of extracted text
        
    Returns:
        Extracted text (truncated if needed)
    """
    doc = Document(file_path)
    text = "\n".join(p.text for p in doc.paragraphs)
    return truncate_text(text, max_length)


def extract_text_from_txt(file_path: str, max_length: int) -> str:
    """
    Extract text from TXT file.
    
    Args:
        file_path: Path to TXT file
        max_length: Maximum length of extracted text
        
    Returns:
        Extracted text (truncated if needed)
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return truncate_text(text, max_length)


async def extract_text_from_file(
    file_content: bytes,
    filename: str,
    max_length: Optional[int] = None
) -> str:
    """
    Extract text from uploaded file (PDF, DOCX, or TXT).
    
    Args:
        file_content: File content as bytes
        filename: Original filename (for extension detection)
        max_length: Maximum length (defaults to Config.MAX_QUERY_LENGTH)
        
    Returns:
        Extracted text
        
    Raises:
        ValueError: If file type is not supported
    """
    if max_length is None:
        max_length = Config.MAX_QUERY_LENGTH
    
    ext = Path(filename).suffix.lower()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name
    
    try:
        if ext == ".pdf":
            return await extract_text_from_pdf(tmp_path, max_length)
        elif ext in (".docx", ".doc"):
            return extract_text_from_docx(tmp_path, max_length)
        elif ext in (".txt", ""):
            return extract_text_from_txt(tmp_path, max_length)
        else:
            raise ValueError(
                f"Unsupported file type: {ext}. Supported types: PDF, DOCX, TXT"
            )
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


