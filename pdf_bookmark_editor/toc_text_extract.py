"""
Extract Table of Contents (TOC) from embedded PDF text and generate TOML bookmarks.

Focuses on text-embedded PDFs (no OCR). Intended to be edited by users before
importing back as PDF bookmarks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
import re

import fitz  # PyMuPDF


@dataclass
class LineInfo:
    text: str
    indent: float
    page_index: int


@dataclass
class TocEntry:
    level: int
    page: int
    title: str
    raw_line: str = ""
    indent: float = 0.0


@dataclass
class ExtractionWarning:
    line: str
    message: str


@dataclass
class ExtractionResult:
    entries: List[TocEntry]
    warnings: List[ExtractionWarning]


class TocTextExtractor:
    """Extract and parse TOC from text-embedded PDFs."""

    PAGE_RE = re.compile(
        r"^(?P<title>.*?)(?:\.{2,}|\s{2,}|\t+)\s*(?P<page>[0-9]{1,5}|[ivxlcdmIVXLCDM]+)\s*$"
    )
    SIMPLE_PAGE_RE = re.compile(
        r"^(?P<title>.+?)\s+(?P<page>[0-9]{1,5}|[ivxlcdmIVXLCDM]+)\s*$"
    )
    PAGE_ONLY_RE = re.compile(r"^(?P<page>[0-9]{1,5}|[ivxlcdmIVXLCDM]+)\s*$")
    NUM_PREFIX_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)*)(?:\s+|[.)])")
    ROMAN_PREFIX_RE = re.compile(r"^(?P<roman>[IVXLCDM]+)(?:\s+|[.)])")
    LETTER_PREFIX_RE = re.compile(r"^(?P<letter>[A-Z])(?:\s+|[.)])")

    def __init__(self, pdf_path: Path | str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

    def extract_to_toml(
        self,
        start_page: int,
        end_page: int,
        output_path: Optional[Path | str] = None,
    ) -> Tuple[Path, ExtractionResult]:
        result = self.extract_entries(start_page, end_page)

        if output_path is None:
            output_path = self.pdf_path.with_suffix(".toc.toml")
        else:
            output_path = Path(output_path)

        self._write_toml(result.entries, output_path)
        return output_path, result

    def extract_entries(self, start_page: int, end_page: int) -> ExtractionResult:
        lines = self._extract_lines(start_page, end_page)
        entries, warnings = self._parse_lines(lines)
        self._infer_levels(entries)
        return ExtractionResult(entries=entries, warnings=warnings)

    def _extract_lines(self, start_page: int, end_page: int) -> List[LineInfo]:
        lines: List[LineInfo] = []

        with fitz.open(self.pdf_path) as pdf:
            total_pages = pdf.page_count
            if start_page < 1 or end_page < 1 or start_page > end_page:
                raise ValueError("Invalid page range for TOC extraction")
            if start_page > total_pages:
                raise ValueError("Start page exceeds PDF page count")
            end_page = min(end_page, total_pages)

            for page_index in range(start_page - 1, end_page):
                page = pdf[page_index]
                blocks = self._get_blocks(page)
                ordered_blocks = self._order_blocks(blocks, page.rect.width)

                for x0, _y0, _x1, _y1, text in ordered_blocks:
                    for raw_line in text.splitlines():
                        clean_line = raw_line.replace("\u00a0", " ")
                        if not clean_line.strip():
                            continue
                        lines.append(
                            LineInfo(
                                text=clean_line.strip(),
                                indent=float(x0),
                                page_index=page_index + 1,
                            )
                        )

        return lines

    def _get_blocks(
        self, page: fitz.Page
    ) -> List[Tuple[float, float, float, float, str]]:
        blocks_raw = page.get_text("blocks")
        blocks: List[Tuple[float, float, float, float, str]] = []
        for block in blocks_raw:
            x0, y0, x1, y1, text = block[:5]
            if text and text.strip():
                blocks.append((x0, y0, x1, y1, text))  # type: ignore
        return blocks

    def _order_blocks(
        self, blocks: List[Tuple[float, float, float, float, str]], page_width: float
    ) -> List[Tuple[float, float, float, float, str]]:
        if not blocks:
            return []
        if len(blocks) < 4:
            return sorted(blocks, key=lambda b: (b[1], b[0]))

        centers = [(b[0] + b[2]) / 2 for b in blocks]
        centers_left = page_width * 0.25
        centers_right = page_width * 0.75
        c1, c2 = centers_left, centers_right

        for _ in range(6):
            cluster1 = []
            cluster2 = []
            for idx, c in enumerate(centers):
                if abs(c - c1) <= abs(c - c2):
                    cluster1.append(idx)
                else:
                    cluster2.append(idx)
            if cluster1:
                c1 = sum(centers[i] for i in cluster1) / len(cluster1)
            if cluster2:
                c2 = sum(centers[i] for i in cluster2) / len(cluster2)

        left_cluster = cluster1 if c1 <= c2 else cluster2
        right_cluster = cluster2 if c1 <= c2 else cluster1

        is_two_column = (
            left_cluster
            and right_cluster
            and abs(c1 - c2) > page_width * 0.25
            and len(left_cluster) >= 2
            and len(right_cluster) >= 2
        )

        if not is_two_column:
            return sorted(blocks, key=lambda b: (b[1], b[0]))

        left_blocks = [blocks[i] for i in left_cluster]
        right_blocks = [blocks[i] for i in right_cluster]
        left_blocks.sort(key=lambda b: (b[1], b[0]))
        right_blocks.sort(key=lambda b: (b[1], b[0]))
        return left_blocks + right_blocks

    def _parse_lines(
        self, lines: Iterable[LineInfo]
    ) -> Tuple[List[TocEntry], List[ExtractionWarning]]:
        entries: List[TocEntry] = []
        warnings: List[ExtractionWarning] = []

        pending_title: Optional[str] = None
        pending_indent: float = 0.0
        pending_raw: str = ""

        for line in lines:
            text = self._normalize_line(line.text)
            if not text:
                continue

            if pending_title:
                page_only = self.PAGE_ONLY_RE.match(text)
                if page_only:
                    page = self._parse_page(page_only.group("page"), warnings, text)
                    if page is not None:
                        entries.append(
                            TocEntry(
                                level=1,
                                page=page,
                                title=pending_title,
                                raw_line=pending_raw,
                                indent=pending_indent,
                            )
                        )
                    pending_title = None
                    continue

                if self._looks_like_continuation(text):
                    pending_title = f"{pending_title} {text}"
                    pending_raw = f"{pending_raw} {text}"
                    continue

                warnings.append(
                    ExtractionWarning(
                        line=pending_raw,
                        message="No page number found for TOC line",
                    )
                )
                pending_title = None

            match = self.PAGE_RE.match(text) or self.SIMPLE_PAGE_RE.match(text)
            if match:
                page = self._parse_page(match.group("page"), warnings, text)
                if page is None:
                    continue
                title = match.group("title").strip()
                if not title:
                    warnings.append(
                        ExtractionWarning(
                            line=text,
                            message="Empty title after parsing",
                        )
                    )
                    continue
                entries.append(
                    TocEntry(
                        level=1,
                        page=page,
                        title=title,
                        raw_line=text,
                        indent=line.indent,
                    )
                )
            else:
                pending_title = text
                pending_indent = line.indent
                pending_raw = text

        if pending_title:
            warnings.append(
                ExtractionWarning(
                    line=pending_raw,
                    message="No page number found for TOC line",
                )
            )

        return entries, warnings

    def _normalize_line(self, text: str) -> str:
        text = text.replace("\t", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _looks_like_continuation(self, text: str) -> bool:
        if self.PAGE_RE.match(text) or self.SIMPLE_PAGE_RE.match(text):
            return False
        if self.NUM_PREFIX_RE.match(text):
            return False
        return len(text) > 3

    def _parse_page(
        self, page_text: str, warnings: List[ExtractionWarning], raw_line: str
    ) -> Optional[int]:
        if page_text.isdigit():
            page = int(page_text)
            if page <= 0:
                warnings.append(
                    ExtractionWarning(
                        line=raw_line,
                        message="Invalid page number (<=0)",
                    )
                )
                return None
            return page

        roman_value = self._roman_to_int(page_text)
        if roman_value is None:
            warnings.append(
                ExtractionWarning(
                    line=raw_line,
                    message=f"Unrecognized page number: {page_text}",
                )
            )
            return None

        warnings.append(
            ExtractionWarning(
                line=raw_line,
                message=f"Roman numeral page converted to {roman_value}",
            )
        )
        return roman_value

    def _roman_to_int(self, roman: str) -> Optional[int]:
        roman = roman.upper()
        roman_map = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        total = 0
        prev = 0
        for ch in reversed(roman):
            if ch not in roman_map:
                return None
            val = roman_map[ch]
            if val < prev:
                total -= val
            else:
                total += val
                prev = val
        return total if total > 0 else None

    def _infer_levels(self, entries: List[TocEntry]) -> None:
        missing_level = []
        for entry in entries:
            level = self._level_from_title(entry.title)
            if level:
                entry.level = level
            else:
                missing_level.append(entry)

        if not missing_level:
            return

        indents = sorted({round(e.indent, 1) for e in missing_level})
        indent_map = {indent: idx + 1 for idx, indent in enumerate(indents)}
        for entry in missing_level:
            entry.level = indent_map.get(round(entry.indent, 1), 1)

    def _level_from_title(self, title: str) -> Optional[int]:
        num_match = self.NUM_PREFIX_RE.match(title)
        if num_match:
            token = num_match.group("num")
            return token.count(".") + 1

        if self.ROMAN_PREFIX_RE.match(title):
            return 1

        if self.LETTER_PREFIX_RE.match(title):
            return 1

        if title.lower().startswith("chapter") or title.lower().startswith("appendix"):
            return 1

        return None

    def _write_toml(self, entries: List[TocEntry], output_path: Path) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f'_comment = "Extracted TOC from {self.pdf_path.name}"\n')
            f.write("_instructions = [\n")
            f.write('    "Edit bookmarks below",\n')
            f.write('    "level: hierarchy level (1=top, 2=sub, 3=sub-sub, etc.)",\n')
            f.write('    "page: physical page number or page-label text (e.g., 12, xviii, A-12)",\n')
            f.write('    "title: bookmark text",\n')
            f.write("\n")
            f.write('    "This file was generated from embedded PDF text.",\n')
            f.write('    "Verify page numbers and hierarchy before importing.",\n')
            f.write('    "page_numbering: relative (default) or absolute",\n')
            f.write("]\n\n")

            f.write('page_numbering = "relative"\n\n')
            f.write("bookmark = [\n")
            
            for entry in entries:
                title = entry.title.replace("\\", "\\\\").replace('"', '\\"')
                f.write(
                    f'    {{ level = {entry.level}, page = {entry.page}, title = "{title}" }},\n'
                )
            f.write("]\n")
