# utils/batch_optimize_images.py
"""
Batch optimize existing product images
Run this script to compress and resize all existing product images
"""

import os
import sys
import shutil

# Add project root to Python path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
from loguru import logger
from utils.paths import app_path
import uuid


def batch_optimize_existing_images(backup_originals=True, target_size=(400, 400), quality=80):
    """
    Optimize all existing product images in the database
    
    Args:
        backup_originals: Whether to backup original images
        target_size: (width, height) tuple for resizing
        quality: JPEG quality (1-100)
    """
    
    images_dir = app_path("database", "product_images")
    if not os.path.exists(images_dir):
        logger.info("No product_images directory found")
        return
    
    # Create backup directory
    backup_dir = os.path.join(images_dir, "backup_originals")
    if backup_originals:
        os.makedirs(backup_dir, exist_ok=True)
    
    optimized_count = 0
    skipped_count = 0
    error_count = 0
    total_size_saved = 0
    
    # Get list of image files
    image_files = []
    for filename in os.listdir(images_dir):
        file_path = os.path.join(images_dir, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
            
        # Skip backup and thumbnail directories
        if filename.startswith('backup_') or filename.startswith('thumb_'):
            continue
            
        # Check if it's an image
        ext = os.path.splitext(filename)[1].lower()
        if ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'):
            image_files.append((file_path, filename, ext))
    
    logger.info(f"Found {len(image_files)} images to process")
    
    for file_path, filename, ext in image_files:
        try:
            original_size = os.path.getsize(file_path)
            
            # Skip if already small enough (under 30KB)
            if original_size < 30 * 1024:
                skipped_count += 1
                logger.debug(f"Skipped {filename}: already small ({original_size//1024}KB)")
                continue
            
            # Open and optimize image
            img = Image.open(file_path)
            
            # Check if image is already optimized (small dimensions)
            if img.width <= target_size[0] and img.height <= target_size[1] and original_size < 100 * 1024:
                skipped_count += 1
                logger.debug(f"Skipped {filename}: already optimized ({img.width}x{img.height}, {original_size//1024}KB)")
                continue
            
            # Resize (maintain aspect ratio)
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Convert RGBA to RGB for JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Backup original
            if backup_originals:
                backup_path = os.path.join(backup_dir, filename)
                shutil.copy2(file_path, backup_path)
            
            # Save optimized version (always as JPEG for smaller size)
            new_filename = os.path.splitext(filename)[0] + '.jpg'
            new_path = os.path.join(images_dir, new_filename)
            
            # If filename changed, remove old file later
            old_path = file_path
            
            # Save with compression
            img.save(new_path, 'JPEG', quality=quality, optimize=True)
            
            # Remove original if different name
            if old_path != new_path and os.path.exists(old_path):
                os.remove(old_path)
            
            new_size = os.path.getsize(new_path)
            size_saved = original_size - new_size
            total_size_saved += size_saved
            
            optimized_count += 1
            logger.info(f"Optimized: {filename} → {new_filename} ({original_size//1024}KB → {new_size//1024}KB, saved {size_saved//1024}KB)")
            
        except Exception as e:
            error_count += 1
            logger.error(f"Failed to optimize {filename}: {e}")
    
    # Summary
    logger.info("=" * 50)
    logger.info("BATCH OPTIMIZATION COMPLETE")
    logger.info(f"  Optimized: {optimized_count} images")
    logger.info(f"  Skipped: {skipped_count} images")
    logger.info(f"  Errors: {error_count} images")
    logger.info(f"  Total space saved: {total_size_saved // (1024*1024)} MB")
    logger.info("=" * 50)


def optimize_single_image(image_path, target_size=(400, 400), quality=80):
    """
    Optimize a single image
    
    Args:
        image_path: Path to image file
        target_size: (width, height) tuple
        quality: JPEG quality (1-100)
    
    Returns:
        Path to optimized image
    """
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return None
    
    try:
        original_size = os.path.getsize(image_path)
        img = Image.open(image_path)
        
        # Resize
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Generate output path
        base_dir = os.path.dirname(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(base_dir, f"{base_name}_optimized.jpg")
        
        # Save
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        new_size = os.path.getsize(output_path)
        logger.info(f"Optimized: {os.path.basename(image_path)} ({original_size//1024}KB → {new_size//1024}KB)")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to optimize image: {e}")
        return None


def cleanup_unused_images():
    """
    Remove product images that are not referenced in the database
    This helps clean up orphaned images
    """
    from models.database import connect_db
    
    images_dir = app_path("database", "product_images")
    if not os.path.exists(images_dir):
        logger.info("No product_images directory found")
        return
    
    # Skip directories
    skip_dirs = {'backup_originals', 'thumbnails', 'optimized'}
    
    try:
        # Get all images from database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT image FROM products WHERE image IS NOT NULL AND image != ''")
        db_images = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        logger.info(f"Found {len(db_images)} images referenced in database")
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        logger.warning("Skipping cleanup due to database error")
        return
    
    removed_count = 0
    removed_size = 0
    
    for filename in os.listdir(images_dir):
        file_path = os.path.join(images_dir, filename)
        
        if os.path.isdir(file_path):
            continue
        
        # Skip backup and thumbnail directories
        if filename.startswith('backup_') or filename.startswith('thumb_'):
            continue
            
        # Check if this image is referenced in database
        is_used = False
        for db_img in db_images:
            if filename in db_img or db_img.endswith(filename):
                is_used = True
                break
        
        if not is_used:
            # Also check if optimized version is used (for PNG -> JPG conversions)
            if filename.endswith('.jpg') and not filename.startswith('thumb_'):
                # Check if original might be used
                original_name = filename.replace('.jpg', '')
                for db_img in db_images:
                    if original_name in db_img or original_name == db_img:
                        is_used = True
                        break
            
        if not is_used:
            try:
                size = os.path.getsize(file_path)
                os.remove(file_path)
                removed_count += 1
                removed_size += size
                logger.debug(f"Removed unused image: {filename} ({size//1024}KB)")
            except Exception as e:
                logger.error(f"Failed to remove {filename}: {e}")
    
    if removed_count > 0:
        logger.info(f"Cleanup complete: removed {removed_count} unused images ({removed_size//(1024*1024)} MB freed)")
    else:
        logger.info("No unused images found")


# ========== RUN SCRIPT ==========
if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("Product Image Batch Optimizer")
    print("=" * 50)
    print()
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        print("Running cleanup of unused images...")
        cleanup_unused_images()
    else:
        print("Optimizing all product images...")
        print("Target size: 400x400")
        print("JPEG Quality: 80")
        print()
        
        response = input("Continue? (y/n): ")
        if response.lower() == 'y':
            batch_optimize_existing_images(
                backup_originals=True,
                target_size=(400, 400),
                quality=80
            )
            
            print()
            response = input("Clean up unused images? (y/n): ")
            if response.lower() == 'y':
                cleanup_unused_images()
        else:
            print("Cancelled.")