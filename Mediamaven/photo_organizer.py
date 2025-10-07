#!/usr/bin/env python3
"""
Photo Organizer Script
Moves photos from multiple source directories to organized YYYY/MM structure
Sources: /media3/immich-app/library/library/admin and /media3/Photos/uploads
Extracts date from EXIF data or falls back to file modification time
Handles duplicate filenames by adding -001, -002, etc suffixes
"""

import os
import shutil
import re
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Try to import PIL for EXIF data
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL/Pillow not installed. Will use file modification dates instead of EXIF data.")
    print("Install with: pip install Pillow")

def get_exif_date(filepath):
    """Extract date from EXIF data if available"""
    if not HAS_PIL:
        return None
    
    try:
        image = Image.open(filepath)
        exif_data = image._getexif()
        
        if exif_data:
            # Try different date tags
            for tag_id in [36867, 36868, 306]:  # DateTimeOriginal, DateTimeDigitized, DateTime
                if tag_id in exif_data:
                    date_str = exif_data[tag_id]
                    # Parse EXIF date format: "YYYY:MM:DD HH:MM:SS"
                    try:
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        continue
    except Exception as e:
        # Silently fail and fall back to file date
        pass
    
    return None

def get_file_date(filepath):
    """Get date from file - tries EXIF first, then modification time"""
    # Try EXIF data first
    exif_date = get_exif_date(filepath)
    if exif_date:
        return exif_date
    
    # Fall back to file modification time
    timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(timestamp)

def get_next_filename(destination_path):
    """
    Generate next available filename with -001, -002, etc suffix if file exists
    Case-insensitive duplicate checking
    """
    if not destination_path.exists():
        # Check case-insensitive duplicates
        parent_dir = destination_path.parent
        base_name = destination_path.stem.lower()
        extension = destination_path.suffix.lower()
        
        if parent_dir.exists():
            existing_files = [f.name.lower() for f in parent_dir.iterdir() if f.is_file()]
            target_name = f"{base_name}{extension}"
            
            if target_name not in existing_files:
                return destination_path
    
    # File exists (case-insensitive), find next available number
    base_name = destination_path.stem
    extension = destination_path.suffix
    parent_dir = destination_path.parent
    counter = 1
    
    while True:
        new_name = f"{base_name}-{counter:03d}{extension}"
        new_path = parent_dir / new_name
        
        # Check case-insensitive
        if parent_dir.exists():
            existing_files = [f.name.lower() for f in parent_dir.iterdir() if f.is_file()]
            if new_name.lower() not in existing_files:
                return new_path
        else:
            return new_path
        
        counter += 1
        if counter > 999:  # Safety break
            raise Exception(f"Too many duplicates for {base_name}")

def is_image_file(filepath):
    """Check if file is an image based on extension"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
                       '.webp', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw', '.dng'}
    return filepath.suffix.lower() in image_extensions

def is_video_file(filepath):
    """Check if file is a video based on extension"""
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.mpg', '.mpeg', 
                       '.wmv', '.flv', '.webm', '.3gp'}
    return filepath.suffix.lower() in video_extensions

def organize_photos_from_source(source_path, dest_path, dry_run=False, include_videos=False):
    """
    Process photos from a single source directory
    Returns: (moved_count, skipped_count, error_count)
    """
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    if not source_path.exists():
        print(f"Source path does not exist: {source_path}")
        return (0, 0, 0)
    
    # Walk through all files in the source directory
    for root, dirs, files in os.walk(source_path):
        root_path = Path(root)
        
        for filename in files:
            source_file = root_path / filename
            
            # Check if it's an image (or video if enabled)
            is_media = is_image_file(source_file) or (include_videos and is_video_file(source_file))
            
            if not is_media:
                print(f"Skipping non-media file: {source_file}")
                skipped_count += 1
                continue
            
            try:
                # Get the date from the file
                file_date = get_file_date(source_file)
                year = file_date.strftime("%Y")
                month = file_date.strftime("%m")
                
                # Create destination directory path
                dest_dir = dest_path / year / month
                
                # Determine final destination filename
                initial_dest_file = dest_dir / filename
                final_dest_file = get_next_filename(initial_dest_file)
                
                if dry_run:
                    print(f"[DRY RUN] Would move: {source_file}")
                    print(f"           -> {final_dest_file} ({year}-{month})")
                    moved_count += 1
                else:
                    # Create destination directory if it doesn't exist
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Move the file
                    shutil.move(str(source_file), str(final_dest_file))
                    print(f"Moved: {source_file}")
                    print(f"    -> {final_dest_file} ({year}-{month})")
                    moved_count += 1
                    
            except Exception as e:
                print(f"Error processing {source_file}: {e}")
                error_count += 1
    
    return (moved_count, skipped_count, error_count)

def organize_photos(sources, destination_base, dry_run=False, include_videos=False):
    """
    Move photos from multiple source directories to organized YYYY/MM structure
    
    Args:
        sources: List of source directories
        destination_base: Base path like /media3/Photos
        dry_run: If True, only show what would be moved without actually moving
        include_videos: If True, also organize video files
    """
    dest_path = Path(destination_base)
    
    total_moved = 0
    total_skipped = 0
    total_errors = 0
    
    for source in sources:
        source_path = Path(source)
        print(f"\n{'='*60}")
        print(f"Processing source: {source_path}")
        print(f"{'='*60}")
        
        moved, skipped, errors = organize_photos_from_source(
            source_path, dest_path, dry_run, include_videos
        )
        
        total_moved += moved
        total_skipped += skipped
        total_errors += errors
        
        print(f"\nSource summary for {source_path}:")
        print(f"  Files moved: {moved}")
        print(f"  Files skipped: {skipped}")
        print(f"  Errors: {errors}")
    
    print(f"\n{'='*60}")
    print(f"OVERALL SUMMARY:")
    print(f"{'='*60}")
    print(f"Total files moved: {total_moved}")
    print(f"Total files skipped: {total_skipped}")
    print(f"Total errors: {total_errors}")
    
    if dry_run:
        print("\nThis was a dry run. Use --execute to actually move files.")

def cleanup_empty_directories(base_paths):
    """Remove empty directories after moving files"""
    for base_path in base_paths:
        base = Path(base_path)
        
        if not base.exists():
            continue
            
        print(f"\nCleaning up empty directories in: {base}")
        
        # Walk bottom-up to remove empty directories
        for root, dirs, files in os.walk(base, topdown=False):
            root_path = Path(root)
            
            # Skip the base directory itself
            if root_path == base:
                continue
                
            try:
                # Try to remove directory if it's empty
                if not any(root_path.iterdir()):
                    root_path.rmdir()
                    print(f"Removed empty directory: {root_path}")
            except OSError:
                # Directory not empty or other error, ignore
                pass

def main():
    parser = argparse.ArgumentParser(
        description='Organize photos from multiple sources into YYYY/MM structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process both default sources (dry run)
  %(prog)s
  
  # Process both sources and actually move files
  %(prog)s --execute
  
  # Process only Immich library
  %(prog)s --source immich --execute
  
  # Process only uploads folder
  %(prog)s --source uploads --execute
  
  # Process custom source
  %(prog)s --source /custom/path --execute
        """
    )
    parser.add_argument('--source', 
                       default='both',
                       help='Source to process: "immich", "uploads", "both", or custom path (default: both)')
    parser.add_argument('--destination',
                       default='/media3/Photos', 
                       help='Destination base directory (default: /media3/Photos)')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Show what would be moved without actually moving files')
    parser.add_argument('--execute',
                       action='store_true', 
                       help='Actually move the files (opposite of dry-run)')
    parser.add_argument('--cleanup-empty',
                       action='store_true',
                       help='Remove empty directories after moving files')
    parser.add_argument('--include-videos',
                       action='store_true',
                       help='Also organize video files')
    
    # Handle no arguments case
    if len(sys.argv) == 1:
        print("No arguments provided. Running dry-run with default paths.")
        print("Use --help to see all options, or --execute to actually move files.")
        print()
        args = argparse.Namespace(
            source='both',
            destination='/media3/Photos', 
            dry_run=True,
            execute=False,
            cleanup_empty=False,
            include_videos=False
        )
        dry_run = True
    else:
        args = parser.parse_args()
        dry_run = not args.execute
    
    if dry_run and not args.dry_run:
        print("Running in DRY RUN mode by default. Use --execute to actually move files.")
        print()
    
    # Determine source directories
    sources = []
    if args.source == 'both':
        sources = [
            '/media3/immich-app/library/library/admin',
            '/media3/Photos/uploads'
        ]
    elif args.source == 'immich':
        sources = ['/media3/immich-app/library/library/admin']
    elif args.source == 'uploads':
        sources = ['/media3/Photos/uploads']
    else:
        # Custom path
        sources = [args.source]
    
    print(f"Destination: {args.destination}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"Include videos: {args.include_videos}")
    if HAS_PIL:
        print("EXIF support: Enabled (will use photo dates from EXIF)")
    else:
        print("EXIF support: Disabled (will use file modification dates)")
    print(f"\nSources to process:")
    for source in sources:
        print(f"  - {source}")
    print("-" * 60)
    
    organize_photos(sources, args.destination, dry_run, args.include_videos)
    
    if args.cleanup_empty and not dry_run:
        print("\nCleaning up empty directories...")
        cleanup_empty_directories(sources)

if __name__ == "__main__":
    main()
