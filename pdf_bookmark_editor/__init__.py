"""
PDF Bookmark Editor

A clean, simple tool for editing PDF bookmarks and page labels using TOML format.
Export bookmarks to TOML, edit in any text editor, then import back.
"""

from .core import BookmarkEditor
from .toc_text_extract import TocTextExtractor

__version__ = "1.0.0"
__all__ = ["BookmarkEditor", "TocTextExtractor"]
