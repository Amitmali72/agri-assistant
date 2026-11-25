"""
Agricultural Document Ingestion Script (Module 5).
Extracts, cleans, hashes, chunks, embeds, and indexes agricultural PDFs into FAISS
and records full provenance metadata into SQLite.
"""

import sys
import os
import argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from backend.config import settings
from backend.services.document_processor import process_pdf, compute_file_hash
from backend.services.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.database.db import save_document_metadata, init_db, get_document_by_hash


def ingest_single_pdf(
    pdf_path: str,
    source_name: str,
    topic: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    publisher: str = "",
    source_url: str = "",
    publication_date: str = "2025-2026",
    language: str = "en",
    crop: str = "",
    region: str = "Maharashtra",
    approval_status: str = "approved",
    version: str = "1.0",
) -> int:
    print(f"\n[Ingest] Processing: {pdf_path}")
    file_hash = compute_file_hash(pdf_path)
    filename = os.path.basename(pdf_path)

    existing = get_document_by_hash(file_hash)
    if existing and existing.get("filename") == filename and vector_store.total_documents > 0:
        # Still ensure vector store actually has this filename
        has_vecs = any(m.get("filename") == filename for m in vector_store.all_metadata)
        if has_vecs:
            print(f"[Ingest] Skipping unchanged file (SHA-256 match): {filename}")
            return 0

    chunks = process_pdf(
        pdf_path,
        source_name=source_name,
        topic=topic,
        publisher=publisher or source_name,
        source_url=source_url,
        publication_date=publication_date,
        language=language,
        crop=crop,
        region=region,
        approval_status=approval_status,
        version=version,
        chunk_size=settings.CHUNK_SIZE,
        overlap=settings.CHUNK_OVERLAP,
    )
    if not chunks:
        print(f"[Ingest] Warning: No readable text extracted from {pdf_path}")
        return 0

    # Replace any stale chunks for same filename
    vector_store.remove_by_filename(filename, embedding_service=embedding_service)

    texts = [c["text"] for c in chunks]
    embeddings = embedding_service.encode(texts)
    vector_store.add_documents(chunks, embeddings=embeddings)

    pages_count = max([c["metadata"].get("page", 1) for c in chunks], default=1)
    save_document_metadata(
        filename=filename,
        source=source_name,
        pages=pages_count,
        topic=topic,
        title=filename,
        publisher=publisher or source_name,
        source_url=source_url,
        publication_date=publication_date,
        language=language,
        crop=crop,
        region=region,
        chunks_count=len(chunks),
        approval_status=approval_status,
        version=version,
        file_hash=file_hash,
    )
    print(f"[Ingest] Indexed {len(chunks)} chunks from {filename} (status={approval_status}).")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description="Ingest agricultural PDFs into KrishiMitra vector store.")
    parser.add_argument("--pdf", type=str, help="Path to a single PDF document.")
    parser.add_argument("--dir", type=str, help="Directory containing PDF documents.")
    parser.add_argument("--source", type=str, default="ICAR / MPKV Rahuri", help="Source / Publisher name.")
    parser.add_argument("--url", type=str, default="https://icar.org.in", help="Official source URL.")
    parser.add_argument("--date", type=str, default="2025-2026", help="Publication date.")
    parser.add_argument("--crop", type=str, default="", help="Primary crop tag.")
    parser.add_argument("--region", type=str, default="Maharashtra", help="Target region/state.")
    parser.add_argument("--lang", type=str, default="en", help="Document language code.")
    parser.add_argument("--topic", type=str, default="general_agriculture", help="Topic category.")
    parser.add_argument("--status", type=str, default="approved", choices=["approved", "pending"], help="Approval status.")
    args = parser.parse_args()

    if not args.pdf and not args.dir:
        parser.print_help()
        sys.exit(1)

    init_db()
    embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
    vector_store = VectorStore(storage_path=settings.VECTOR_STORE_PATH)

    total_chunks = 0
    if args.pdf:
        total_chunks += ingest_single_pdf(
            args.pdf, args.source, args.topic, embedding_service, vector_store,
            publisher=args.source, source_url=args.url, publication_date=args.date,
            language=args.lang, crop=args.crop, region=args.region, approval_status=args.status,
        )
    if args.dir:
        for pdf_path in sorted(Path(args.dir).glob("*.pdf")):
            total_chunks += ingest_single_pdf(
                str(pdf_path), args.source, args.topic, embedding_service, vector_store,
                publisher=args.source, source_url=args.url, publication_date=args.date,
                language=args.lang, crop=args.crop, region=args.region, approval_status=args.status,
            )

    vector_store.save()
    print(f"\nIngestion Complete! New chunks: {total_chunks} | Total vectors: {vector_store.total_documents}")


if __name__ == "__main__":
    main()
