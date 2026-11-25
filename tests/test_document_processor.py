"""
Tests for PDF Document Processing, Cleaning, and Chunking.
"""

import os
import pytest
from backend.services.document_processor import clean_text, chunk_text, extract_text_from_pdf, process_pdf


def test_clean_text():
    raw = "  कांदा  पिकामध्ये \t खत व्यवस्थापन.\n\n\n\nपाणी नियोजन.  "
    cleaned = clean_text(raw)
    assert "कांदा पिकामध्ये खत व्यवस्थापन." in cleaned
    assert "पाणी नियोजन." in cleaned
    assert "\n\n\n" not in cleaned
    assert "\t" not in cleaned


def test_chunk_text():
    sample = (
        "गव्हाच्या पिकाला पेरणीनंतर २१ दिवसांनी पहिले पाणी द्यावे. "
        "या अवस्थेला मुकुट मुळे फुटण्याची अवस्था (CRI) म्हणतात. "
    ) * 10
    chunks = chunk_text(sample, chunk_size=200, overlap=30)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 300
        assert len(chunk) >= 20


def test_extract_and_process_pdf():
    pdf_path = "data/raw_pdfs/wheat_and_paddy_cultivation_handbook.pdf"
    if os.path.exists(pdf_path):
        pages = extract_text_from_pdf(pdf_path)
        assert len(pages) >= 1
        assert "Wheat" in pages[0]["text"] or "Paddy" in pages[0]["text"]

        chunks = process_pdf(pdf_path, source_name="Test Source", topic="wheat")
        assert len(chunks) >= 1
        assert chunks[0]["metadata"]["source"] == "Test Source"
        assert chunks[0]["metadata"]["topic"] == "wheat"
