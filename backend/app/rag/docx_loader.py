"""Load a ``.docx`` file into an ordered list of titled sections.

A *section* is a heading paragraph plus every paragraph that follows it until the
next heading.  Paragraphs that appear before the first heading (or documents with
no headings at all) are collected under a single ``"Document"`` section so that
downstream code never has to special-case the "no headings" document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

DEFAULT_SECTION_TITLE = "Document"


@dataclass
class Section:
    """A titled slice of the document.

    Attributes:
        title: The heading text, or ``"Document"`` for the implicit lead section.
        body: The section's plain-text content with paragraphs joined by newlines.
    """

    title: str
    lines: list[str] = field(default_factory=list)

    @property
    def body(self) -> str:
        """The section content as a single newline-joined string."""
        return "\n".join(line for line in self.lines if line.strip())


def _is_heading(paragraph: Paragraph) -> bool:
    """True when a paragraph uses a Word built-in heading style (``Heading 1`` ...)."""
    style_name = (paragraph.style.name or "") if paragraph.style else ""
    return style_name.lower().startswith("heading") or style_name.lower() == "title"


def _iter_block_text(document: Document) -> list[str]:
    """Yield the document body as text lines, flattening tables to ``" | "`` rows.

    ``python-docx`` exposes paragraphs and tables separately; this helper walks the
    underlying XML body so paragraph/table order is preserved.  Table rows are kept
    because they frequently hold the facts a presenter is asked about.
    """
    lines: list[str] = []
    parent_elm = document.element.body
    for child in parent_elm.iterchildren():
        if child.tag.endswith("}p"):
            para = Paragraph(child, document)
            marker = "\x00HEADING\x00" if _is_heading(para) else ""
            lines.append(f"{marker}{para.text}")
        elif child.tag.endswith("}tbl"):
            table = Table(child, document)
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    lines.append(" | ".join(cells))
    return lines


def load_docx(path: str | Path) -> list[Section]:
    """Parse ``path`` and return its sections in document order.

    Args:
        path: Path to a ``.docx`` file.

    Returns:
        A non-empty list of :class:`Section`.  Sections whose body is empty
        (a heading with no content) are dropped.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    document = Document(str(path))
    sections: list[Section] = [Section(title=DEFAULT_SECTION_TITLE)]

    for raw_line in _iter_block_text(document):
        if raw_line.startswith("\x00HEADING\x00"):
            heading_text = raw_line.removeprefix("\x00HEADING\x00").strip()
            if heading_text:
                sections.append(Section(title=heading_text))
            continue
        text = raw_line.strip()
        if text:
            sections[-1].lines.append(text)

    non_empty = [section for section in sections if section.body]
    return non_empty or [Section(title=DEFAULT_SECTION_TITLE, lines=["(empty document)"])]
