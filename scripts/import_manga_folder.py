#!/usr/bin/env python3
"""Import manga pages from a folder (webp, png, jpg supported).

Usage:
    python scripts/import_manga_folder.py /path/to/manga/folder "Manga Title"

The script will:
1. Scan the folder for supported image files
2. Sort them naturally by filename
3. Import them as a manga volume
4. Save to manga storage for UI access
5. Optionally create a graph node
6. Display the ingestion report
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.archivist import (
    SUPPORTED_MANGA_IMAGE_EXTENSIONS,
    DEFAULT_INGESTION_POLICY,
    IngestionPolicy,
    ingest_image_folder_pages,
    list_manga_image_pages,
)
from core.manga_storage import get_manga_storage, MangaVolume, MangaPage


def main() -> int:
    parser = argparse.ArgumentParser(description="Import manga pages from a folder")
    parser.add_argument(
        "folder",
        type=Path,
        help="Path to folder containing manga pages",
    )
    parser.add_argument(
        "title",
        nargs="?",
        default=None,
        help="Manga title (defaults to folder name)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without importing",
    )
    parser.add_argument(
        "--no-graph-node",
        action="store_true",
        help="Don't create a graph node for this manga",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Custom database path (default: .loom/manga.db)",
    )

    args = parser.parse_args()

    folder_path = args.folder.resolve()
    title = args.title or folder_path.name

    # Validate folder
    if not folder_path.exists():
        print(f"❌ Error: Folder not found: {folder_path}")
        return 1

    if not folder_path.is_dir():
        print(f"❌ Error: Not a directory: {folder_path}")
        return 1

    # List pages
    pages = list_manga_image_pages(folder_path)

    if not pages:
        print(f"❌ No supported image files found in: {folder_path}")
        print(f"   Supported formats: {SUPPORTED_MANGA_IMAGE_EXTENSIONS}")
        return 1

    print(f"📁 Folder: {folder_path}")
    print(f"📚 Title: {title}")
    print(f"📄 Pages found: {len(pages)}")
    print()

    # Show first few pages
    print("First 5 pages:")
    for i, page in enumerate(pages[:5], 1):
        print(f"  {i}. {page.name}")
    if len(pages) > 5:
        print(f"  ... and {len(pages) - 5} more")
    print()

    if args.dry_run:
        print("✅ Dry run complete. Use without --dry-run to import.")
        return 0

    # Import with extended timeout for large folders
    print("🔄 Importing pages...")
    print("   (This may take a while for large volumes with OCR)")

    # Use non-sandbox mode with extended timeout for CLI
    policy = IngestionPolicy(
        max_file_size_bytes=100 * 1024 * 1024,  # 100MB
        max_page_count=10_000,
        max_archive_entry_count=10_000,
        max_archive_uncompressed_bytes=2 * 1024 * 1024 * 1024,  # 2GB
        max_compression_ratio=100.0,
        worker_timeout_seconds=300.0,  # 5 minutes for large imports
    )

    try:
        report = ingest_image_folder_pages(
            folder_path,
            policy=policy,
            use_sandbox=False,  # Direct execution for CLI
        )

        print()
        print("=" * 50)
        print("✅ Import successful!")
        print("=" * 50)
        print(f"Pages imported: {report.page_count}")
        print(f"Spreads detected: {report.spread_count}")
        print(f"Source hash: {report.source_hash[:16]}...")

        if report.warnings:
            print()
            print("⚠️  Warnings:")
            for warning in report.warnings:
                print(f"  - {warning}")

        print()
        print("Page details:")
        for i, meta in enumerate(report.page_metadata[:10], 1):
            print(f"  Page {i}: {meta.format_name}, " f"{meta.width}x{meta.height}")
        if len(report.page_metadata) > 10:
            print(f"  ... and {len(report.page_metadata) - 10} more pages")

        # Save to manga storage
        print()
        print("💾 Saving to manga storage...")
        
        storage = get_manga_storage(args.db_path)
        
        # Check for existing volume with same hash
        existing = storage.get_volume_by_hash(report.source_hash)
        if existing:
            print(f"⚠️  A manga with this content already exists: '{existing.title}'")
            print(f"   Volume ID: {existing.volume_id}")
            return 0

        # Create volume record
        volume_id = f"manga_{uuid.uuid4().hex[:12]}"
        
        manga_pages = tuple(
            MangaPage(
                page_number=i + 1,
                format_name=meta.format_name,
                width=meta.width,
                height=meta.height,
                content_hash=meta.content_hash,
                ocr_text=getattr(meta, 'ocr_text', ''),  # OCR text if available
            )
            for i, meta in enumerate(report.page_metadata)
        )

        volume = MangaVolume(
            volume_id=volume_id,
            title=title,
            source_path=str(folder_path),
            page_count=report.page_count,
            source_hash=report.source_hash,
            pages=manga_pages,
        )

        if storage.save_volume(volume):
            print(f"✅ Saved manga volume: {volume_id}")
            print(f"   Title: {title}")
            print(f"   Pages: {report.page_count}")
            
            # Optionally create graph node
            if not args.no_graph_node:
                print()
                print("📝 Creating graph node...")
                try:
                    from core.graph_persistence import SQLiteGraphPersistence, GraphNode
                    
                    graph_db = SQLiteGraphPersistence()
                    
                    # Create a node for this manga
                    node_id = f"node_{uuid.uuid4().hex[:12]}"
                    node = GraphNode(
                        node_id=node_id,
                        label=title,
                        branch_id="main",
                        scene_id=f"scene_{uuid.uuid4().hex[:8]}",
                        x=100.0,
                        y=100.0,
                        importance=0.8,
                        metadata={
                            "type": "manga",
                            "volume_id": volume_id,
                            "page_count": report.page_count,
                            "source_hash": report.source_hash,
                            "source_path": str(folder_path),
                        },
                    )
                    
                    # Use async method in sync context
                    import asyncio
                    success = asyncio.run(graph_db.save_node(node))
                    
                    if success:
                        print(f"✅ Created graph node: {node_id}")
                        print(f"   The manga is now available in the UI!")
                    else:
                        print("⚠️  Failed to create graph node (manga saved to storage)")
                        
                except Exception as e:
                    print(f"⚠️  Could not create graph node: {e}")
                    print("   Manga is saved but won't appear in the graph. Use --no-graph-node to skip this.")
        else:
            print("❌ Failed to save manga volume")
            return 1

        return 0

    except Exception as e:
        print(f"❌ Import failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
