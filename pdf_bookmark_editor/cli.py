#!/usr/bin/env python3
"""
PDF Bookmark Editor - Command Line Tool

Usage:
    pdf-bookmarks export <pdf_file> [--output <file>]
    pdf-bookmarks import <toml_file> <pdf_file> [--output <pdf>]
    pdf-bookmarks extract-toc <pdf_file> <start_page> <end_page> [--output <file>]

Examples:
    # Export bookmarks to TOML
    pdf-bookmarks export book.pdf
    
    # Edit the exported book.bookmarks.toml file, then import back
    pdf-bookmarks import book.bookmarks.toml book.pdf
    
    # Or specify custom output
    pdf-bookmarks import bookmarks.toml book.pdf --output new_book.pdf

    # Extract TOC from embedded text
    pdf-bookmarks extract-toc book.pdf 5 12 --output book.toc.toml
"""

import argparse
import sys
from pathlib import Path
from .core import BookmarkEditor
from .toc_text_extract import TocTextExtractor


def export_command(args):
    """Export bookmarks from PDF"""
    pdf_path = Path(args.pdf_file)
    
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return 1
    
    editor = BookmarkEditor(pdf_path)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.with_suffix('.bookmarks.toml')
    
    try:
        result = editor.export_to_toml(output_path)
        print(f"✅ Exported bookmarks to TOML: {result}")
        
        # Show preview
        import tomli
        with open(result, 'rb') as f:
            data = tomli.load(f)
        bookmark_count = len(data.get('bookmark', []))
        
        print(f"\n📊 Exported {bookmark_count} bookmarks")
        print(f"\n📝 Next steps:")
        print(f"   1. Edit the file: {result}")
        print(f"   2. Import back: pdf-bookmarks import {result} {pdf_path}")
        
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def import_command(args):
    """Import bookmarks to PDF"""
    toml_file = Path(args.toml_file)
    pdf_path = Path(args.pdf_file)
    
    if not toml_file.exists():
        print(f"❌ Error: TOML file not found: {toml_file}")
        return 1
    
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return 1
    
    editor = BookmarkEditor(pdf_path)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.parent / f"{pdf_path.stem}_updated.pdf"
    
    try:
        result = editor.import_from_toml(toml_file, output_path)
        print(f"✅ Imported bookmarks from TOML")
        print(f"📄 Created PDF: {result}")
        print(f"\n🎯 Open the PDF to see your custom bookmarks!")
        
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def extract_toc_command(args):
    """Extract TOC from embedded PDF text"""
    pdf_path = Path(args.pdf_file)

    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return 1

    try:
        extractor = TocTextExtractor(pdf_path)
        output_path, result = extractor.extract_to_toml(
            start_page=int(args.start_page),
            end_page=int(args.end_page),
            output_path=args.output,
        )

        print(f"✅ Extracted TOC to TOML: {output_path}")
        print(f"📊 Extracted {len(result.entries)} entries")

        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings[:10]:
                print(f"   - {warning.message}: {warning.line}")
            if len(result.warnings) > 10:
                print(f"   ... ({len(result.warnings) - 10} more)")

        print("\n📝 Next steps:")
        print(f"   1. Edit the file: {output_path}")
        print(f"   2. Import back: pdf-bookmarks import {output_path} {pdf_path}")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='PDF Bookmark Editor - Export/import bookmarks using TOML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export bookmarks from PDF to TOML')
    export_parser.add_argument('pdf_file', help='Input PDF file')
    export_parser.add_argument('--output', '-o', help='Output TOML file')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import bookmarks from TOML to PDF')
    import_parser.add_argument('toml_file', help='TOML file with bookmarks')
    import_parser.add_argument('pdf_file', help='Input PDF file')
    import_parser.add_argument('--output', '-o', help='Output PDF file')

    # Extract TOC command
    extract_parser = subparsers.add_parser('extract-toc', help='Extract TOC from embedded PDF text')
    extract_parser.add_argument('pdf_file', help='Input PDF file')
    extract_parser.add_argument('start_page', help='Start page of TOC (1-based)')
    extract_parser.add_argument('end_page', help='End page of TOC (1-based)')
    extract_parser.add_argument('--output', '-o', help='Output TOML file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run command
    if args.command == 'export':
        return export_command(args)
    elif args.command == 'import':
        return import_command(args)
    elif args.command == 'extract-toc':
        return extract_toc_command(args)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
