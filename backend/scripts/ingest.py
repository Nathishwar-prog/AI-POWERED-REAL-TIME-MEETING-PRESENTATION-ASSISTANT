"""Ingest a ``.docx`` from the command line and print a summary.

Usage (from the ``backend/`` directory)::

    python -m scripts.ingest sample_data/sample_presentation.docx

Writes the vector store under ``<DATA_DIR>/<doc_id>/`` and prints the section and
chunk counts, plus a preview of each chunk, so retrieval quality can be eyeballed
without starting the server.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.rag.chunker import chunk_sections
from app.rag.docx_loader import load_docx
from app.documents import DocumentRegistry


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = argparse.ArgumentParser(description="Ingest a .docx into a vector store.")
    parser.add_argument("docx", type=Path, help="Path to the .docx file")
    parser.add_argument(
        "--preview-chars", type=int, default=120, help="Characters of each chunk to show"
    )
    args = parser.parse_args(argv)

    if not args.docx.exists():
        parser.error(f"file not found: {args.docx}")

    sections = load_docx(args.docx)
    chunks = chunk_sections(sections)

    print(f"Sections ({len(sections)}):")
    for section in sections:
        print(f"  - {section.title}  ({len(section.body)} chars)")

    print(f"\nChunks ({len(chunks)}):")
    for chunk in chunks:
        preview = chunk.text[: args.preview_chars].replace("\n", " ")
        print(f"  [{chunk.index:>3}] ({chunk.section_title}) {preview}...")

    info = DocumentRegistry().ingest_path(args.docx)
    print(f"\nStored doc_id={info.doc_id}  sections={info.sections}  chunks={info.chunks}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
