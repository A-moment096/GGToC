# PDF Bookmark Editor 🔖

**Clean, simple PDF bookmark editing using TOML format.**

Export PDF bookmarks to TOML, edit them in any text editor, then import back. Perfect for reorganizing, simplifying, or creating bookmarks from scratch.

## ✨ Features

- ✅ **TOML Format** - Modern, clean, easy to edit
- ✅ **Dual Page Numbering** - Shows both physical pages and logical labels (i, ii, 1, 2, etc.)
- ✅ **Correct Page Numbers** - Extracts actual page numbers from PDFs
- ✅ **Simple Structure** - Just title, page, and level
- ✅ **Emoji Support** - Use 📚🎯✨ in bookmark titles
- ✅ **Easy Editing** - Works with any text editor
- ✅ **Fast** - Uses PyMuPDF for performance

## 🚀 Quick Start

### Installation

**Option 1: Install from PyPI (when published)**
```bash
pip install pdf-bookmark-editor
```

**Option 2: Install from source**
```bash
git clone https://github.com/yourusername/pdf-bookmark-editor.git
cd pdf-bookmark-editor
pip install -e .
```

**Option 3: Using uv**
```bash
uv pip install pdf-bookmark-editor
```

### Usage

**Command Line:**

**1. Export bookmarks:**
```bash
pdf-bookmarks export mybook.pdf
# or: uv run pdf-bookmarks export mybook.pdf
```
Creates `mybook.bookmarks.toml`

**2. Edit the TOML file:**
```toml
bookmark = [
    { level = 1, page = "0010", page_label = "1", title = "📚 Chapter 1" },
    { level = 2, page = "0011", page_label = "2", title = "Section 1.1" },
    { level = 2, page = "0015", page_label = "6", title = "Section 1.2" },
    { level = 1, page = "0020", page_label = "11", title = "🎯 Chapter 2" },
]
```

**3. Import back:**
```bash
pdf-bookmarks import mybook.bookmarks.toml mybook.pdf
```
Creates `mybook_updated.pdf` with your bookmarks!

**Python API:**

```python
from pdf_bookmark_editor import BookmarkEditor

# Create editor
editor = BookmarkEditor("mybook.pdf")

# Export to TOML
editor.export_to_toml("bookmarks.toml")

# ... edit bookmarks.toml ...

# Import from TOML
editor.import_from_toml("bookmarks.toml", "output.pdf")
```

## 📝 TOML Format

### Structure

```toml
# Instructions (optional, ignored on import)
_comment = "PDF Bookmarks from mybook.pdf"
_instructions = [
    "Edit bookmarks below",
    "level: hierarchy level (1=top, 2=sub, 3=sub-sub, etc.)",
    "page: physical page number (zero-padded, 1-based)",
    "page_label: logical page label (e.g., \"C1\", \"iv\", \"23\")",
    "title: bookmark text (emoji supported! 📚)",
]

# Bookmarks array
bookmark = [
    { level = 1, page = "0005", page_label = "iv", title = "Preface" },
    { level = 1, page = "0010", page_label = "1", title = "Chapter 1" },
    { level = 2, page = "0011", page_label = "2", title = "Section 1.1" },
    { level = 3, page = "0013", page_label = "4", title = "Subsection" },
]
```

### Fields

- **level**: Hierarchy level (integer, 1=top level, 2=sub, 3=sub-sub, etc.)
- **page**: Physical page number (zero-padded 4-digit string, e.g., "0010")
- **page_label**: Logical page label (string, e.g., "i", "iv", "1", "23", "C1")
- **title**: Bookmark text (string, emoji supported)

### Understanding Page Numbers

PDFs can have **two types** of page numbers:

1. **Physical page** (`page`): The actual position in the PDF file
   - Always starts at 1
   - Zero-padded to 4 digits: "0001", "0010", "0100"
   - Example: Physical page 19 is the 19th page in the file

2. **Logical label** (`page_label`): What you see in your PDF reader
   - Can use Roman numerals (i, ii, iii, ...), Arabic (1, 2, 3, ...), or custom labels
   - Example: A book might have:
     - Cover: "C1"
     - Front matter: "i", "ii", "iii", ... "xvii"
     - Main content: "1", "2", "3", ... "390"

**When editing bookmarks:**
- ✅ Use `page_label` if you know the "human-readable" page (e.g., "page 1" of Chapter 1)
- ✅ Use `page` if you know the exact physical position
- ✅ Both fields are exported for your convenience
- ✅ On import, `page` takes precedence if both are specified

### Advantages of TOML

- ✅ Clean syntax, minimal punctuation
- ✅ Easy to read and edit
- ✅ No indentation issues (unlike YAML)
- ✅ Comments with `#`
- ✅ Modern standard (Rust, Python projects use it)
- ✅ Good editor support

## 💻 Command Line Reference

### Export

```bash
pdf-bookmarks export <pdf_file> [--output <file>]
```

**Examples:**
```bash
# Basic export
pdf-bookmarks export book.pdf

# Custom output
pdf-bookmarks export book.pdf --output bookmarks/my.toml
```

### Import

```bash
pdf-bookmarks import <toml_file> <pdf_file> [--output <pdf>]
```

**Examples:**
```bash
# Basic import (creates book_updated.pdf)
pdf-bookmarks import book.bookmarks.toml book.pdf

# Custom output
pdf-bookmarks import bookmarks.toml book.pdf --output final.pdf
```

## 🐍 Python API

```python
from pdf_bookmark_editor import BookmarkEditor

# Create editor
editor = BookmarkEditor("mybook.pdf")

# Export to TOML
editor.export_to_toml("bookmarks.toml")

# ... edit bookmarks.toml ...

# Import from TOML
editor.import_from_toml("bookmarks.toml", "output.pdf")
```

### API Reference

**`BookmarkEditor(pdf_path)`**
- `pdf_path`: Path to the PDF file (str or Path)

**`export_to_toml(output_path=None)`**
- Exports bookmarks and page labels to TOML format
- `output_path`: Output TOML file path (default: `{pdf_name}.bookmarks.toml`)
- Returns: Path to the created TOML file

**`import_from_toml(toml_path, output_pdf=None)`**
- Imports bookmarks and page labels from TOML and creates new PDF
- `toml_path`: Input TOML file path
- `output_pdf`: Output PDF path (default: `{pdf_name}_updated.pdf`)
- Returns: Path to the created PDF

## 📖 Examples

### Example 1: Simplify Structure

**Before** (169 detailed bookmarks):
```toml
bookmark = [
    { level = 1, page = "0019", page_label = "1", title = "Chapter 1 Vector Spaces" },
    { level = 2, page = "0020", page_label = "2", title = "1A Rⁿ and Cⁿ" },
    { level = 3, page = "0020", page_label = "2", title = "Complex Numbers" },
    { level = 3, page = "0023", page_label = "5", title = "Lists" },
    { level = 3, page = "0024", page_label = "6", title = "Fⁿ" },
    # ... 164 more ...
]
```

**After** (30 clean bookmarks):
```toml
bookmark = [
    { level = 1, page_label = "1", title = "1️⃣ Chapter 1: Vector Spaces" },
    { level = 2, page_label = "2", title = "1A Fundamentals" },
    { level = 2, page_label = "30", title = "1B Definitions" },
    { level = 2, page_label = "36", title = "1C Subspaces" },
]
```

Note: You can omit `page` and use only `page_label` for easier editing!

### Example 2: Add Visual Organization

```toml
bookmark = [
    { level = 1, page_label = "i", title = "📚 Part I: Theory" },
    { level = 2, page_label = "1", title = "Chapter 1" },
    { level = 2, page_label = "30", title = "Chapter 2" },
    
    { level = 1, page_label = "50", title = "🔬 Part II: Applications" },
    { level = 2, page_label = "51", title = "Chapter 3" },
    
    { level = 1, page_label = "100", title = "🎯 Part III: Reference" },
    { level = 2, page_label = "101", title = "Index" },
]
```

### Example 3: Create from Scratch

```toml
# Add bookmarks to a PDF that has none
bookmark = [
    { level = 1, page = "0001", title = "Cover" },
    { level = 1, page = "0002", title = "Table of Contents" },
    { level = 1, page = "0005", title = "Introduction" },
    { level = 1, page = "0010", title = "Main Content" },
    { level = 1, page = "0050", title = "Conclusion" },
]
```

### Example 4: Working with Roman Numerals

```toml
# Books with front matter often use Roman numerals
bookmark = [
    { level = 1, page_label = "i", title = "Title Page" },
    { level = 1, page_label = "iii", title = "Dedication" },
    { level = 1, page_label = "v", title = "Preface" },
    { level = 1, page_label = "ix", title = "Contents" },
    { level = 1, page_label = "1", title = "Chapter 1" },  # Main content starts
]
```

## 🎨 Use Cases

1. **Simplify overly detailed bookmarks** - 200 → 20 bookmarks
2. **Add emoji for categorization** - 📚📝🎯✨
3. **Fix incorrect page numbers** - Quick edits
4. **Standardize structure** - Apply to multiple similar PDFs
5. **Create bookmarks** - For PDFs without any
6. **Bulk editing** - Sort, filter, reorganize easily
7. **Version control** - Track changes in git

## 🔧 Technical Details

- **PDF Library**: PyMuPDF (fitz) - fast, accurate
- **TOML Libraries**: tomli (read), tomli-w (write)
- **Page Numbers**: 1-based (first page = 1)
- **Order**: Bookmarks appear in file order
- **Validation**: Page numbers should be within PDF page count

## 💡 Tips

### Tip 1: Use VS Code

Install the "Even Better TOML" extension for syntax highlighting and validation.

### Tip 2: Bulk Editing

Open TOML in Excel or text editor with column mode for quick edits:
```toml
{ level = 1, page_label = "10", title = "Ch 1" },
{ level = 1, page_label = "20", title = "Ch 2" },
{ level = 1, page_label = "30", title = "Ch 3" },
```

### Tip 3: Version Control

```bash
git add mybook.bookmarks.toml
git commit -m "Simplified bookmarks"
git diff  # See what changed!
```

### Tip 4: Templates

Save common structures:
```toml
# template.toml
bookmark = [
    { level = 1, page = "0001", title = "Cover" },
    { level = 1, page = "0002", title = "Contents" },
    { level = 1, page_label = "1", title = "Chapter 1" },
    # ... edit pages and labels as needed ...
]
```

### Tip 5: Use Logical Labels for Easier Editing

When editing, it's often easier to think in terms of logical page labels:
- Instead of: "Chapter 1 starts on physical page 19"
- Think: "Chapter 1 starts on page_label '1'"

The tool will automatically resolve "1" → physical page 19.

## 🆚 Why TOML over Other Formats?

| Format | Pros | Cons |
|--------|------|------|
| **TOML** | Clean, modern, easy | Slightly verbose |
| Markdown | Familiar `#` syntax | Not structured data |
| YAML | Human-readable | Indentation errors |
| JSON | Universal | Too many quotes/braces |
| CSV | Excel-compatible | No hierarchy viz |

TOML hits the sweet spot: **structured but readable**.

## 📂 Project Structure

```
GGToC/
├── bookmark_editor.py      # Core library
├── pdf_bookmarks.py        # CLI tool
├── resources/
│   └── test-LADR.pdf       # Your PDF
└── output/
    ├── bookmarks.toml      # Exported bookmarks
    └── edited_bookmarks.toml  # Example
```

## 🐛 Troubleshooting

**Page numbers wrong?**
- The exported file shows both `page` (physical) and `page_label` (logical)
- Use `page_label` if you want to reference "page 1" as seen in your PDF reader
- Use `page` for exact physical position in the file
- Physical page 1 = first page of PDF file
- Logical label "1" might correspond to physical page 19 (if there's front matter)

**Import fails?**
- Check TOML syntax (use validator)
- Verify page numbers/labels are valid
- Ensure all required fields present (level, title, and either page or page_label)

**Bookmarks not showing?**
- Try different PDF viewer
- Close and reopen PDF
- Check original PDF supports bookmarks

**Page labels not working?**
- Not all PDFs have page labels defined
- Export will show same value for both `page` and `page_label` if no labels exist
- You can still use physical page numbers

## 📄 License

MIT License - Free to use!

---

**Made with ❤️ for clean, simple PDF organization** 🔖✨
