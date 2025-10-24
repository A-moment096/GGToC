# PDF Bookmark Editor - Package Summary

## 📦 Package Structure

```
pdf-bookmark-editor/
├── pdf_bookmark_editor/          # Main package
│   ├── __init__.py              # Package exports
│   ├── core.py                  # BookmarkEditor class
│   └── cli.py                   # Command-line interface
├── resources/                    # Test resources
│   └── test-LADR.pdf
├── output/                       # Output directory
├── pyproject.toml               # Package metadata & dependencies
├── LICENSE                      # MIT License
├── README.md                    # Full documentation
├── MANIFEST.in                  # Package manifest
├── .gitignore                   # Git ignore rules
└── example.py                   # Usage example
```

## 🚀 Installation

### From Source (Development)
```bash
git clone <repository>
cd pdf-bookmark-editor
pip install -e .
```

### From PyPI (when published)
```bash
pip install pdf-bookmark-editor
```

## 📚 Usage

### Command Line
```bash
# Export bookmarks
pdf-bookmarks export mybook.pdf

# Import bookmarks
pdf-bookmarks import mybook.bookmarks.toml mybook.pdf
```

### Python API
```python
from pdf_bookmark_editor import BookmarkEditor

editor = BookmarkEditor("mybook.pdf")
editor.export_to_toml("bookmarks.toml")
# ... edit TOML ...
editor.import_from_toml("bookmarks.toml", "output.pdf")
```

## 🔧 Features

✅ Export PDF bookmarks to clean TOML format
✅ Import edited bookmarks back to PDF
✅ Page label support (Roman numerals, prefixes)
✅ Handles both proper and malformed page labels
✅ Command-line interface
✅ Python library API
✅ Zero-padded page numbers for alignment
✅ Emoji support in titles

## 📋 Dependencies

- PyMuPDF >= 1.26.5 (PDF manipulation)
- tomli >= 2.3.0 (TOML reading, Python < 3.11)
- tomli-w >= 1.2.0 (TOML writing)

## 🔨 Building & Publishing

### Build Package
```bash
python -m build
```

### Publish to PyPI
```bash
python -m twine upload dist/*
```

## 📄 License

MIT License - See LICENSE file

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows PEP 8
- Add tests for new features
- Update documentation
