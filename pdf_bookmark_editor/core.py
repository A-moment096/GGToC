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

        # Convert bookmarks to TOML structure
        bookmarks = []
        for level, title, page in toc:
            bookmarks.append({"level": level, "page": page, "title": title})

        pdf.close()

        # Write TOML with custom formatting
        with open(output_path, "w", encoding="utf-8") as f:
            # Write header
            f.write(f'_comment = "PDF Bookmarks from {self.pdf_path.name}"\n')
            f.write("_instructions = [\n")
            f.write('    "Edit bookmarks below",\n')
            f.write('    "level: hierarchy level (1=top, 2=sub, 3=sub-sub, etc.)",\n')
            f.write('    "page: page number (1-based)",\n')
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
            f.write("]\n\n")

            # Write page labels section if any exist (array-of-tables must come after inline arrays)
            if page_label_ranges:
                for i, label_range in enumerate(page_label_ranges):
                    f.write("[[page_label]]\n")
                    f.write(f'start = {label_range["start"]}\n')
                    f.write(f'style = "{label_range["style"]}"\n')
                    if label_range["prefix"]:
                        f.write(f'prefix = "{label_range["prefix"]}"\n')
                    if label_range["first"] != 1:
                        f.write(f'first = {label_range["first"]}\n')
                    f.write("\n")

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

        # Convert bookmarks to TOC format
        toc = []
        for bm in bookmarks:
            level = bm.get("level", 1)
            page = bm.get("page", 1)
            title = bm.get("title", "Untitled")
            toc.append([level, title, page])

        # Create output PDF
        if output_pdf is None:
            output_pdf = self.pdf_path.parent / f"{self.pdf_path.stem}_updated.pdf"
        else:
            output_pdf = Path(output_pdf)

        # Apply bookmarks and page labels to PDF
        pdf = fitz.open(self.pdf_path)
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
