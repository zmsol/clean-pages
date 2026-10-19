"""Convert EPUB and PDF files to Markdown (narrative "meat" only by default)."""

from __future__ import annotations

import re
from pathlib import Path

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    _EPUB_AVAILABLE = True
except ImportError:
    _EPUB_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text as _pdfminer_extract_text
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

try:
    import html2text
    _HTML2TEXT_AVAILABLE = True
except ImportError:
    _HTML2TEXT_AVAILABLE = False


JUNK_TOKENS = (
    "cover", "titlepage", "title-page", "half-title", "halftitle", "colophon",
    "copyright", "dedication", "frontmatter", "front-matter", "disclaimer",
    "contents", "toc", "nav", "appendix", "acknowledg", "note", "endnote",
    "index.html", "index.xhtml", "toc.html", "toc.xhtml", "nav.xhtml",
    "about", "backmatter", "back-matter", "glossary",
    "bibliography", "foreword", "preface", "praise", "advertisement",
    "errata", "promo", "backad",
)

_TOC_LINE = re.compile(r"^.{1,90}?\.{2,}\s*\d{1,5}\s*$")
_LETTERSPACED = re.compile(r"(?<![A-Za-z])(?:[A-Za-z] ){3,}[A-Za-z](?![A-Za-z])")
_WS = re.compile(r"[ \t]+")


def _make_html2text(ignore_links: bool) -> "html2text.HTML2Text":
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = ignore_links
    h.ignore_images = True
    h.ignore_tables = False
    h.single_line_break = False
    h.unicode_snob = True
    h.baseurl = ""
    return h


def _repair_letterspacing(text: str) -> str:
    return _LETTERSPACED.sub(lambda m: m.group(0).replace(" ", ""), text)


def _clean_markdown(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip() + "\n"


def _is_junk_spine_item(item_id: str, href: str) -> bool:
    low = (item_id + " " + href).lower()
    return any(tok in low for tok in JUNK_TOKENS)


def _epub_to_md(path: Path, meat: bool, keep_links: bool) -> str:
    if not _EPUB_AVAILABLE:
        raise RuntimeError("EPUB support requires ebooklib and beautifulsoup4.")
    if not _HTML2TEXT_AVAILABLE:
        raise RuntimeError("EPUB support requires html2text.")

    book = epub.read_epub(str(path))
    h = _make_html2text(ignore_links=not keep_links)

    title = None
    for meta in book.get_metadata("DC", "title"):
        if meta and meta[0]:
            title = meta[0]
            break

    blocks: list[str] = []
    if title:
        blocks.append(f"# {title}\n")

    seen = set()
    for item in book.spine:
        item_id = item[0]
        doc = book.get_item_with_id(item_id)
        if doc is None or doc.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        href = doc.get_name()
        if meat and _is_junk_spine_item(item_id, href):
            continue
        content = doc.get_content()
        if content in seen:
            continue
        seen.add(content)
        try:
            soup = BeautifulSoup(content, "html.parser")
        except Exception:
            continue
        for tag in soup(["script", "style", "head"]):
            tag.decompose()
        md = h.handle(str(soup)).strip()
        if md:
            blocks.append(md)

    return _clean_markdown(_repair_letterspacing("\n\n".join(blocks)))


def _pdf_to_md(path: Path, meat: bool, keep_links: bool) -> str:
    if not _PDF_AVAILABLE:
        raise RuntimeError("PDF support requires pdfminer.six.")

    raw = _pdfminer_extract_text(str(path)) or ""
    raw = raw.replace("\u2028", "\n").replace("\r\n", "\n").replace("\r", "\n")

    meta = {}
    try:
        from pdfminer.pdfparser import PDFParser
        from pdfminer.pdfdocument import PDFDocument
        from pdfminer.pdftypes import resolve1
        with open(path, "rb") as fh:
            parser = PDFParser(fh)
            doc = PDFDocument(parser)
            if doc.info:
                for k, v in doc.info[0].items():
                    try:
                        meta[k.lower()] = str(resolve1(v))
                    except Exception:
                        pass
    except Exception:
        meta = {}

    title = meta.get("title")

    blocks: list[str] = []
    if title:
        blocks.append(f"# {title}\n")

    for line in raw.splitlines():
        line = _WS.sub(" ", line).strip()
        if not line:
            continue
        if meat and _TOC_LINE.match(line):
            continue
        blocks.append(line)

    return _clean_markdown("\n\n".join(blocks))


def convert_to_markdown(path: Path, meat: bool = True, keep_links: bool = False) -> str:
    suffix = path.suffix.lower()
    if suffix == ".epub":
        return _epub_to_md(path, meat=meat, keep_links=keep_links)
    if suffix == ".pdf":
        return _pdf_to_md(path, meat=meat, keep_links=keep_links)
    raise ValueError(f"Unsupported file type: {path.name!r} (expected .epub or .pdf)")
