"""Tests for :mod:`app.rag.docx_loader`."""

from __future__ import annotations

from pathlib import Path

from app.rag.docx_loader import DEFAULT_SECTION_TITLE, load_docx


def test_load_docx_splits_on_headings(sample_docx: Path) -> None:
    sections = load_docx(sample_docx)
    titles = [section.title for section in sections]
    assert titles == ["Refund Policy", "Shipping", "Support Hours"]


def test_section_body_contains_paragraph_text(sample_docx: Path) -> None:
    sections = {section.title: section.body for section in load_docx(sample_docx)}
    assert "30 days" in sections["Refund Policy"]
    assert "next day" in sections["Shipping"]


def test_document_without_headings_yields_single_section(tmp_path: Path) -> None:
    from docx import Document

    document = Document()
    document.add_paragraph("Just a plain paragraph with no heading.")
    path = tmp_path / "plain.docx"
    document.save(str(path))

    sections = load_docx(path)
    assert len(sections) == 1
    assert sections[0].title == DEFAULT_SECTION_TITLE
    assert "plain paragraph" in sections[0].body


def test_missing_file_raises(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(FileNotFoundError):
        load_docx(tmp_path / "nope.docx")
