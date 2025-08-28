#!/usr/bin/env python3
"""
Immich Video Organizer Script
Moves videos from Immich's admin structure to organized Photos/videos directory
Handles duplicate filenames by adding -001, -002, etc suffixes
"""

import os
import shutil
import re
import sys
from pathlib import Path
import argparse

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

def is_video_file(filepath):
    """Check if file is a video based on extension"""
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', 
                       '.m4v', '.3gp', '.3g2', '.asf', '.rm', '.rmvb', '.vob',
                       '.ts', '.mts', '.m2ts', '.divx', '.xvid', '.f4v', '.ogv'}
    return filepath.suffix.lower() in video_extensions

def move_videos(source_base, destination_base, dry_run=False):
    """
    Move videos from Immich admin structure to organized Photos/videos directory
    
    Args:
        source_base: Base path like /media3/immich-app/library/library/admin
        destination_base: Base path like /media3/Photos/uploads/videos
        dry_run: If True, only show what would be moved without actually moving
    """
    source_path = Path(source_base)
    dest_path = Path(destination_base)
    
    if not source_path.exists():
        print(f"Source path does not exist: {source_path}")
        return
    
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    # Walk through all files in the admin directory structure
    for root, dirs, files in os.walk(source_path):
        root_path = Path(root)
        
        # Skip if not in YYYY/MM structure
        relative_path = root_path.relative_to(source_path)
        path_parts = relative_path.parts
        
        # Look for YYYY/MM pattern
        if len(path_parts) >= 2:
            year_part = path_parts[-2]
            month_part = path_parts[-1]
            
            # Validate YYYY/MM pattern
            if (re.match(r'^\d{4}$', year_part) and 
                re.match(r'^\d{2}$', month_part)):
                
                year = year_part
                month = month_part
                
                # Create destination directory
                dest_dir = dest_path / year / month
                
                for filename in files:
                    source_file = root_path / filename
                    
                    # Only process video files
                    if not is_video_file(source_file):
                        print(f"Skipping non-video file: {source_file}")
                        skipped_count += 1
                        continue
                    
                    # Determine destination filename
                    initial_dest_file = dest_dir / filename
                    final_dest_file = get_next_filename(initial_dest_file)
                    
                    try:
                        if dry_run:
                            print(f"[DRY RUN] Would move: {source_file} -> {final_dest_file}")
                            moved_count += 1
                        else:
                            # Create destination directory if it doesn't exist
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Move the file
                            shutil.move(str(source_file), str(final_dest_file))
                            print(f"Moved: {source_file} -> {final_dest_file}")
                            moved_count += 1
                        
                    except Exception as e:
                        print(f"Error moving {source_file}: {e}")
                        error_count += 1
    
    print(f"\nSummary:")
    print(f"Videos processed: {moved_count}")
    print(f"Files skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    
    if dry_run:
        print("\nThis was a dry run. Use --execute to actually move files.")

def cleanup_empty_directories(base_path):
    """Remove empty directories after moving files"""
    base = Path(base_path)
    
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
    parser = argparse.ArgumentParser(description='Move Immich videos to organized directory structure')
    parser.add_argument('--source', 
                       default='/media3/immich-app/library/library/admin',
                       help='Source directory (default: /media3/immich-app/library/library/admin)')
    parser.add_argument('--destination',
                       default='/media3/Photos/uploads/videos', 
                       help='Destination directory (default: /media3/Photos/uploads/videos)')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Show what would be moved without actually moving files')
    parser.add_argument('--execute',
                       action='store_true', 
                       help='Actually move the files (opposite of dry-run)')
    parser.add_argument('--cleanup-empty',
                       action='store_true',
                       help='Remove empty directories after moving files')
    
    # Make script executable directly
    if len(sys.argv) == 1:
        # No arguments provided, show help and run dry-run
        print("No arguments provided. Running dry-run with default paths.")
        print("Use --help to see all options, or --execute to actually move files.")
        print()
        args = argparse.Namespace(
            source='/media3/immich-app/library/library/admin',
            destination='/media3/Photos/uploads/videos', 
            dry_run=True,
            execute=False,
            cleanup_empty=False
        )
        dry_run = True
    else:
        args = parser.parse_args()
        # Default to dry run unless --execute is specified
        dry_run = not args.execute
    
    if dry_run and not args.dry_run:
        print("Running in DRY RUN mode by default. Use --execute to actually move files.")
        print()
    
    print(f"Source: {args.source}")
    print(f"Destination: {args.destination}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print("-" * 50)
    
    move_videos(args.source, args.destination, dry_run)
    
    if args.cleanup_empty and not dry_run:
        print("\nCleaning up empty directories...")
        cleanup_empty_directories(args.source)

if __name__ == "__main__":
    main()
