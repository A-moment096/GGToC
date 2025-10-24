#!/usr/bin/env python3
"""
Quick example of using pdf-bookmark-editor as a Python library
"""

from pdf_bookmark_editor import BookmarkEditor
from pathlib import Path

def main():
    # Example PDF path
    pdf_path = Path("resources/test-LADR.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        print("Please provide a valid PDF path")
        return
    
    # Create editor
    print(f"📖 Opening PDF: {pdf_path}")
    editor = BookmarkEditor(pdf_path)
    
    # Export to TOML
    toml_path = pdf_path.with_suffix('.bookmarks.toml')
    print(f"📤 Exporting bookmarks to: {toml_path}")
    result = editor.export_to_toml(toml_path)
    print(f"✅ Exported successfully!")
    
    # You can now edit the TOML file manually
    print(f"\n💡 Next steps:")
    print(f"   1. Edit {toml_path}")
    print(f"   2. Run: editor.import_from_toml('{toml_path}', 'output.pdf')")

if __name__ == "__main__":
    main()
