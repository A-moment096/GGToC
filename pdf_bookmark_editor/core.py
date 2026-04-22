"""
PDF Bookmark Editor - TOML Format

Export PDF bookmarks to TOML format, edit them, then import back.
Uses PyMuPDF for accurate page numbers and TOML for clean editing.
"""

import fitz  # PyMuPDF
import tomli
import tomli_w
from pathlib import Path
from typing import Union


class BookmarkEditor:
    """Export/import PDF bookmarks and page labels using TOML format"""

    def __init__(self, pdf_path: Union[str, Path]):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

    def _preferred_decimal_ranges(self, page_label_ranges: list) -> list[dict]:
        """Return normalized decimal page-label ranges, preferring empty-prefix ranges."""
        normalized = []
        for label_range in page_label_ranges:
            if not isinstance(label_range, dict):
                continue
            try:
                start = int(label_range.get("start", 1))
                first = int(label_range.get("first", 1))
            except (TypeError, ValueError):
                continue

            style = str(label_range.get("style", "decimal"))
            prefix = str(label_range.get("prefix", ""))
            if style != "decimal":
                continue

            normalized.append(
                {
                    "start": max(1, start),
                    "first": max(1, first),
                    "prefix": prefix,
                }
            )

        if not normalized:
            return []

        normalized.sort(key=lambda x: x["start"])
        empty_prefix = [r for r in normalized if not r["prefix"]]
        return empty_prefix or normalized

    def _absolute_to_relative_page(
        self, absolute_page: int, page_label_ranges: list, page_count: int
    ) -> int:
        """Convert a physical page number to a logical decimal page label value."""
        if absolute_page < 1:
            return 1

        ranges = self._preferred_decimal_ranges(page_label_ranges)
        if not ranges:
            return min(absolute_page, page_count)

        for idx, label_range in enumerate(ranges):
            start = label_range["start"]
            first = label_range["first"]
            next_start = ranges[idx + 1]["start"] if idx + 1 < len(ranges) else page_count + 1
            if start <= absolute_page < next_start:
                return first + (absolute_page - start)

        return min(absolute_page, page_count)

    def _relative_to_absolute_page(
        self, relative_page: int, page_label_ranges: list, page_count: int
    ) -> int:
        """Convert a logical decimal page label value to a physical page number."""
        if relative_page < 1:
            return 1

        ranges = self._preferred_decimal_ranges(page_label_ranges)
        if not ranges:
            return min(relative_page, page_count)

        for idx, label_range in enumerate(ranges):
            start = label_range["start"]
            first = label_range["first"]
            next_start = ranges[idx + 1]["start"] if idx + 1 < len(ranges) else page_count + 1
            candidate = start + (relative_page - first)
            if start <= candidate < next_start:
                return max(1, min(candidate, page_count))

        # Fallback: map using the first preferred decimal range.
        first_range = ranges[0]
        candidate = first_range["start"] + (relative_page - first_range["first"])
        return max(1, min(candidate, page_count))

    def _to_roman(self, number: int, uppercase: bool = False) -> str:
        """Convert positive integer to Roman numeral."""
        if number <= 0:
            return ""

        vals = [
            (1000, "M"),
            (900, "CM"),
            (500, "D"),
            (400, "CD"),
            (100, "C"),
            (90, "XC"),
            (50, "L"),
            (40, "XL"),
            (10, "X"),
            (9, "IX"),
            (5, "V"),
            (4, "IV"),
            (1, "I"),
        ]
        out = []
        remaining = number
        for value, symbol in vals:
            while remaining >= value:
                out.append(symbol)
                remaining -= value
            if remaining == 0:
                break
        result = "".join(out)
        return result if uppercase else result.lower()

    def _build_label_to_page_map(self, page_label_ranges: list, page_count: int) -> dict[str, int]:
        """Build map from rendered page labels to physical page numbers."""
        if page_count <= 0:
            return {}

        normalized = []
        for label_range in page_label_ranges:
            if not isinstance(label_range, dict):
                continue

            try:
                start = int(label_range.get("start", 1))
                first = int(label_range.get("first", 1))
            except (TypeError, ValueError):
                continue

            normalized.append(
                {
                    "start": max(1, min(start, page_count)),
                    "style": str(label_range.get("style", "decimal")),
                    "prefix": str(label_range.get("prefix", "")),
                    "first": max(1, first),
                }
            )

        if not normalized:
            return {}

        normalized.sort(key=lambda x: x["start"])
        label_map: dict[str, int] = {}

        for idx, label_range in enumerate(normalized):
            start = label_range["start"]
            next_start = (
                normalized[idx + 1]["start"] if idx + 1 < len(normalized) else page_count + 1
            )
            style = label_range["style"]
            prefix = label_range["prefix"]
            first = label_range["first"]

            for physical_page in range(start, min(next_start, page_count + 1)):
                offset = physical_page - start
                label_number = first + offset

                if style == "roman":
                    label = f"{prefix}{self._to_roman(label_number, uppercase=False)}"
                elif style == "ROMAN":
                    label = f"{prefix}{self._to_roman(label_number, uppercase=True)}"
                elif style == "decimal":
                    label = f"{prefix}{label_number}"
                else:
                    # style "none" has no unique numbering; skip ambiguous reverse mapping
                    continue

                if label and label not in label_map:
                    label_map[label] = physical_page

        return label_map

    def _resolve_bookmark_page(
        self,
        page_value: Union[int, str],
        page_numbering: str,
        page_label_ranges: list,
        page_count: int,
    ) -> int:
        """Resolve bookmark page value (numeric or label text) to physical page."""
        if isinstance(page_value, int):
            numeric_page = page_value
        else:
            text = str(page_value).strip()
            if not text:
                numeric_page = 1
            elif text.isdigit():
                numeric_page = int(text)
            else:
                if page_numbering == "absolute":
                    raise ValueError(
                        f"Invalid absolute page value '{page_value}'. Use integer physical page number."
                    )

                label_map = self._build_label_to_page_map(page_label_ranges, page_count)
                exact = label_map.get(text)
                if exact is not None:
                    return exact

                # Fallback case-insensitive lookup to be editor-friendly.
                lowered = text.lower()
                for label, physical_page in label_map.items():
                    if label.lower() == lowered:
                        return physical_page

                raise ValueError(
                    f"Could not resolve page label '{page_value}' using page_label definitions."
                )

        if page_numbering == "relative":
            return self._relative_to_absolute_page(numeric_page, page_label_ranges, page_count)

        return max(1, min(numeric_page, page_count))

    def export_to_toml(self, output_path: Union[str, Path, None] = None) -> Path:
        """
        Export bookmarks and page labels to TOML format.
        """
        if output_path is None:
            output_path = self.pdf_path.with_suffix(".bookmarks.toml")
        else:
            output_path = Path(output_path)

        # Get bookmarks from PDF
        pdf = fitz.open(self.pdf_path)
        toc = pdf.get_toc()  # Returns [[level, title, page], ...]

        # Extract page label ranges from PDF metadata
        # Handle both proper page labels (with style field) and malformed ones (prefix-only)
        page_labels_raw = pdf.get_page_labels()
        page_label_ranges = []

        # Roman numeral generator
        def generate_roman_numerals(n: int) -> list[str]:
            """Generate lowercase roman numerals for 1..n."""
            vals = [
                (1000, "M"),
                (900, "CM"),
                (500, "D"),
                (400, "CD"),
                (100, "C"),
                (90, "XC"),
                (50, "L"),
                (40, "XL"),
                (10, "X"),
                (9, "IX"),
                (5, "V"),
                (4, "IV"),
                (1, "I"),
            ]

            def int_to_roman(num: int) -> str:
                res = []
                for value, symbol in vals:
                    while num >= value:
                        res.append(symbol)
                        num -= value
                    if num == 0:
                        break
                return "".join(res).lower()

            return [int_to_roman(i) for i in range(1, max(0, n) + 1)]

        # Generate roman numerals up to 100 for pattern matching
        roman_numerals = generate_roman_numerals(100)

        if page_labels_raw:
            i = 0
            while i < len(page_labels_raw):
                label_info = page_labels_raw[i]
                start_page = label_info.get("startpage", 0) + 1
                prefix = label_info.get("prefix", "").strip()
                style_code = label_info.get("style", "")
                first_num = label_info.get("firstpagenum", 1)

                # Case 1: Proper style-based label
                if style_code:
                    # Has proper style field - just use it
                    if style_code == "r":
                        style_str = "roman"
                    elif style_code == "R":
                        style_str = "ROMAN"
                    elif style_code == "D":
                        style_str = "decimal"
                    else:
                        style_str = "none"

                    page_label_ranges.append(
                        {
                            "start": start_page,
                            "style": style_str,
                            "prefix": prefix,
                            "first": first_num,
                        }
                    )
                    i += 1

                # Case 2: Malformed - detect pattern from prefixes
                else:
                    # Check for lowercase roman numerals
                    if prefix.lower() in roman_numerals:
                        # Find where roman numerals end
                        end_idx = i
                        while end_idx < len(page_labels_raw):
                            next_prefix = (
                                page_labels_raw[end_idx]
                                .get("prefix", "")
                                .strip()
                                .lower()
                            )
                            if next_prefix not in roman_numerals:
                                break
                            end_idx += 1

                        page_label_ranges.append(
                            {
                                "start": start_page,
                                "style": "roman",
                                "prefix": "",
                                "first": 1,
                            }
                        )
                        i = end_idx

                    # Check for decimal numbers
                    elif prefix.isdigit():
                        # Find where numbers end
                        end_idx = i
                        while end_idx < len(page_labels_raw):
                            next_prefix = (
                                page_labels_raw[end_idx].get("prefix", "").strip()
                            )
                            if not next_prefix.isdigit():
                                break
                            end_idx += 1

                        page_label_ranges.append(
                            {
                                "start": start_page,
                                "style": "decimal",
                                "prefix": "",
                                "first": int(prefix),
                            }
                        )
                        i = end_idx

                    # Check for prefix + number (like "C1", "A2", "B-5")
                    else:
                        import re

                        match = re.match(r"^([A-Za-z\-]+)(\d+)$", prefix)
                        if match:
                            letter_prefix = match.group(1)
                            first_num = int(match.group(2))

                            # Find where this pattern ends
                            end_idx = i
                            while end_idx < len(page_labels_raw):
                                next_prefix = (
                                    page_labels_raw[end_idx].get("prefix", "").strip()
                                )
                                next_match = re.match(
                                    r"^([A-Za-z\-]+)(\d+)$", next_prefix
                                )
                                if (
                                    not next_match
                                    or next_match.group(1) != letter_prefix
                                ):
                                    break
                                end_idx += 1

                            page_label_ranges.append(
                                {
                                    "start": start_page,
                                    "style": "decimal",
                                    "prefix": letter_prefix,
                                    "first": first_num,
                                }
                            )
                            i = end_idx
                        else:
                            # Static label - no numbering
                            page_label_ranges.append(
                                {
                                    "start": start_page,
                                    "style": "none",
                                    "prefix": prefix,
                                    "first": 1,
                                }
                            )
                            i += 1

        # Convert bookmarks to TOML structure (default to relative logical pages)
        bookmarks = []
        for level, title, page in toc:
            relative_page = self._absolute_to_relative_page(page, page_label_ranges, pdf.page_count)
            bookmarks.append({"level": level, "page": relative_page, "title": title})

        pdf.close()

        # Write TOML with custom formatting
        with open(output_path, "w", encoding="utf-8") as f:
            # Write header
            f.write(f'_comment = "PDF Bookmarks from {self.pdf_path.name}"\n')
            f.write("_instructions = [\n")
            f.write('    "Edit bookmarks below",\n')
            f.write('    "level: hierarchy level (1=top, 2=sub, 3=sub-sub, etc.)",\n')
            f.write('    "page: physical page number or page-label text (e.g., 12, xviii, A-12)",\n')
            f.write('    "title: bookmark text",\n')
            f.write('    "",\n')
            f.write(
                '    "Page labels (optional): define how page numbers are displayed in PDF viewer",\n'
            )
            f.write('    "  start: first physical page of this range",\n')
            f.write(
                '    "  style: roman (i,ii,iii), ROMAN (I,II,III), decimal (1,2,3), or none",\n'
            )
            f.write('    "  prefix: text before number (e.g., C, A-, Chapter )",\n')
            f.write('    "  first: starting number for this range (default: 1)",\n')
            f.write('    "",\n')
            f.write('    "Page numbering mode for bookmark.page:",\n')
            f.write('    "  page_numbering = relative (default): page is logical/printed number",\n')
            f.write('    "  page_numbering = absolute: page is physical PDF page number",\n')
            f.write("]\n\n")

            f.write('page_numbering = "relative"\n\n')

            # Write bookmarks (inline array must come before array-of-tables)
            f.write("bookmark = [\n")
            for bm in bookmarks:
                level = bm["level"]
                page = bm["page"]
                title = (
                    bm["title"].replace("\\", "\\\\").replace('"', '\\"')
                )  # Escape backslashes first, then quotes
                f.write(
                    f'    {{ level = {level}, page = {page}, title = "{title}" }},\n'
                )
            f.write("]\n\n")

            # Write page labels section if any exist.
            # Keep this after bookmark so unqualified keys remain at root.
            if page_label_ranges:
                for label_range in page_label_ranges:
                    f.write("[[page_label]]\n")
                    f.write(f'start = {label_range["start"]}\n')
                    f.write(f'style = "{label_range["style"]}"\n')
                    if label_range["prefix"]:
                        f.write(f'prefix = "{label_range["prefix"]}"\n')
                    if label_range["first"] != 1:
                        f.write(f'first = {label_range["first"]}\n')
                    f.write("\n")

        return output_path

    def import_from_toml(
        self, toml_path: Union[str, Path], output_pdf: Union[str, Path, None] = None
    ) -> Path:
        """
        Import bookmarks from TOML format and create new PDF.
        Supports both physical page numbers and logical page labels.
        """
        toml_path = Path(toml_path)
        if not toml_path.exists():
            raise FileNotFoundError(f"TOML file not found: {toml_path}")

        # Read TOML
        with open(toml_path, "rb") as f:
            data = tomli.load(f)

        bookmarks = data.get("bookmark", [])
        page_label_ranges = data.get("page_label", [])
        page_numbering = str(data.get("page_numbering", "relative")).strip().lower()

        if page_numbering not in {"relative", "absolute"}:
            raise ValueError(
                "Invalid page_numbering. Use 'relative' or 'absolute'."
            )

        # Backward compatibility: if bookmark was written after [[page_label]],
        # TOML parsers place it inside the last page_label table instead of root.
        if not bookmarks and isinstance(page_label_ranges, list):
            for label_range in page_label_ranges:
                if not isinstance(label_range, dict):
                    continue
                nested_bookmarks = label_range.get("bookmark")
                if isinstance(nested_bookmarks, list) and nested_bookmarks:
                    bookmarks = nested_bookmarks
                    break

        if not bookmarks:
            raise ValueError(
                "No bookmarks found in TOML. Ensure 'bookmark = [...]' is at root level "
                "(before any [[page_label]] tables)."
            )

        # Create output PDF
        if output_pdf is None:
            output_pdf = self.pdf_path.parent / f"{self.pdf_path.stem}_updated.pdf"
        else:
            output_pdf = Path(output_pdf)

        # Apply bookmarks and page labels to PDF
        pdf = fitz.open(self.pdf_path)

        # Convert bookmarks to TOC format
        toc = []
        for bm in bookmarks:
            level = int(bm.get("level", 1))
            page_value = bm.get("page", 1)
            title = bm.get("title", "Untitled")

            page = self._resolve_bookmark_page(
                page_value=page_value,
                page_numbering=page_numbering,
                page_label_ranges=page_label_ranges,
                page_count=pdf.page_count,
            )

            toc.append([level, title, page])

        pdf.set_toc(toc)

        # Apply page labels if defined
        if page_label_ranges:
            label_data = []
            for label_range in page_label_ranges:
                start = label_range.get("start", 1) - 1  # Convert 1-based to 0-based
                style_str = label_range.get("style", "decimal")
                prefix = label_range.get("prefix", "")
                first = label_range.get("first", 1)

                # Convert style string to PyMuPDF format
                if style_str == "roman":
                    style = "r"
                elif style_str == "ROMAN":
                    style = "R"
                elif style_str == "decimal":
                    style = "D"
                else:
                    style = ""  # No numbering

                label_data.append(
                    {
                        "startpage": start,
                        "prefix": prefix,
                        "style": style,
                        "firstpagenum": first,
                    }
                )

            pdf.set_page_labels(label_data)

        pdf.save(output_pdf)
        pdf.close()

        return output_pdf


def main():
    """Demo the bookmark editor"""
    print("=" * 70)
    print("PDF Bookmark Editor - TOML Format")
    print("=" * 70)

    pdf_path = Path("resources/test-LADR.pdf")
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return

    editor = BookmarkEditor(pdf_path)
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Export
    print("\n📤 Exporting bookmarks to TOML...")
    toml_file = output_dir / "bookmarks.toml"
    result = editor.export_to_toml(toml_file)
    print(f"✅ Exported to: {result}")

    # Show preview
    print("\n📄 Preview (first 50 lines):")
    print("-" * 70)
    with open(result, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:50]):
            print(line.rstrip())
        if len(lines) > 50:
            print(f"... ({len(lines) - 50} more lines)")

    # Count bookmarks
    with open(result, "rb") as f:
        data = tomli.load(f)
        bookmark_count = len(data.get("bookmark", []))

    print(f"\n📊 Exported {bookmark_count} bookmarks")
    print("\n" + "=" * 70)
    print("✅ Edit the TOML file and import with:")
    print(f"   editor.import_from_toml('{result}', 'output.pdf')")
    print("=" * 70)


if __name__ == "__main__":
    main()
