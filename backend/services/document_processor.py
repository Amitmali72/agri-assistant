"""
Document Processor Service
Extracts, cleans, and chunks text from PDF files using PyMuPDF (pymupdf/fitz).
Supports:
- SHA-256 duplicate detection
- Provenance metadata (publisher, source_url, publication_date, language, crop, region, approval_status, version)
- Optional OCR fallback for scanned PDF pages if pytesseract/PIL are installed
"""

import re
import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_text_from_pdf(pdf_path: str, enable_ocr: bool = True) -> List[Dict[str, Any]]:
    """
    Extract text from all pages of a PDF.
    Falls back to OCR via pytesseract if a page appears to be scanned/image-only
    and pytesseract is available.
    Returns a list of dicts: {page_num, text, ocr_used, metadata}
    """
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz  # PyMuPDF fallback
        except ImportError:
            raise ImportError("PyMuPDF is required. Install with: pip install pymupdf")

    pages = []
    pdf_path = str(pdf_path)

    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            text = page.get_text("text") or ""
            ocr_used = False

            # OCR fallback for scanned PDFs when text is essentially empty
            if enable_ocr and len(text.strip()) < 20:
                ocr_text = _try_ocr_page(page)
                if ocr_text:
                    text = ocr_text
                    ocr_used = True

            pages.append({
                "page_num": page_num + 1,
                "text": text,
                "ocr_used": ocr_used,
                "metadata": {
                    "page": page_num + 1,
                    "total_pages": total_pages,
                    "filename": os.path.basename(pdf_path),
                    "filepath": pdf_path,
                }
            })
        doc.close()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF '{pdf_path}': {e}")

    return pages


def _try_ocr_page(page) -> str:
    """Attempt OCR on a scanned PDF page using pytesseract if installed."""
    try:
        import pytesseract
        from PIL import Image
        import io

        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang="eng+hin+mar")
    except Exception:
        return ""


def clean_text(text: str) -> str:
    """
    Clean extracted text: remove extra whitespace, fix common encoding issues.
    Preserves Devanagari and other Unicode characters.
    """
    if not text:
        return ""

    text = text.replace('\x00', '').replace('\ufffd', '')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks of approximately chunk_size characters.
    Splits at paragraph and sentence boundaries (including Devanagari danda '।').
    """
    if not text:
        return []

    chunks = []
    paragraphs = re.split(r'\n\s*\n', text)
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(para) > chunk_size:
            sentences = re.split(r'(?<=[.?!।])\s+', para)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                    current_chunk = (current_chunk + " " + sentence).strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                        overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                        current_chunk = (overlap_text + " " + sentence).strip()
                    else:
                        step = max(chunk_size - overlap, 50)
                        for i in range(0, len(sentence), step):
                            sub = sentence[i:i + chunk_size]
                            if sub:
                                chunks.append(sub)
                        current_chunk = ""
        else:
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk = (current_chunk + "\n\n" + para).strip() if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = (overlap_text + " " + para).strip()
                else:
                    current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return [c for c in chunks if len(c.strip()) >= 20]


def process_pdf(
    pdf_path: str,
    source_name: str,
    topic: Optional[str] = None,
    publisher: Optional[str] = None,
    source_url: Optional[str] = None,
    publication_date: Optional[str] = None,
    language: str = "en",
    crop: Optional[str] = None,
    region: str = "India",
    approval_status: str = "approved",
    version: str = "1.0",
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Full pipeline: extract -> clean -> chunk a PDF with rich provenance metadata.
    """
    pdf_path = str(pdf_path)
    filename = os.path.basename(pdf_path)
    pages = extract_text_from_pdf(pdf_path)

    all_chunks = []
    global_chunk_id = 0

    for page_data in pages:
        page_num = page_data["page_num"]
        cleaned = clean_text(page_data["text"])
        if not cleaned:
            continue

        chunks = chunk_text(cleaned, chunk_size=chunk_size, overlap=overlap)
        for chunk in chunks:
            all_chunks.append({
                "text": chunk,
                "metadata": {
                    "source": source_name,
                    "publisher": publisher or source_name,
                    "source_url": source_url or "",
                    "publication_date": publication_date or "",
                    "language": language,
                    "crop": crop or "",
                    "region": region,
                    "approval_status": approval_status,
                    "version": version,
                    "page": page_num,
                    "chunk_id": global_chunk_id,
                    "topic": topic or "general",
                    "filename": filename,
                    "filepath": pdf_path,
                }
            })
            global_chunk_id += 1

    return all_chunks


class DocumentProcessor:
    """Wrapper class providing document extraction, cleaning, hashing, and chunking methods."""

    def compute_hash(self, pdf_path: str) -> str:
        return compute_file_hash(pdf_path)

    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        return extract_text_from_pdf(pdf_path)

    def clean_text(self, text: str) -> str:
        return clean_text(text)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        return chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    def process_pdf(
        self,
        pdf_path: str,
        source_name: str,
        topic: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        return process_pdf(pdf_path, source_name=source_name, topic=topic, **kwargs)
