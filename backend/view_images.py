#!/usr/bin/env python3
"""
Script to view and list downloaded satellite images
"""

import os
import glob
from datetime import datetime

def list_images():
    """List all downloaded satellite images"""
    images_dir = os.path.join(os.path.dirname(__file__), "images")
    
    if not os.path.exists(images_dir):
        print("❌ Images directory not found!")
        return
    
    print(f"📁 Images Directory: {images_dir}")
    print("=" * 60)
    
    # Get all image files
    image_files = glob.glob(os.path.join(images_dir, "*.png"))
    
    if not image_files:
        print("📭 No images found in the directory")
        return
    
    # Group images by type
    image_types = {}
    for img_path in image_files:
        filename = os.path.basename(img_path)
        parts = filename.split('_')
        if len(parts) >= 3:
            img_type = parts[0]  # dsm, rgb, or mask
            timestamp = '_'.join(parts[1:]).replace('.png', '')
            
            if img_type not in image_types:
                image_types[img_type] = []
            
            # Get file size
            file_size = os.path.getsize(img_path)
            file_size_mb = file_size / (1024 * 1024)
            
            image_types[img_type].append({
                'filename': filename,
                'path': img_path,
                'timestamp': timestamp,
                'size_mb': file_size_mb
            })
    
    # Display images by type
    for img_type in sorted(image_types.keys()):
        print(f"\n🖼️ {img_type.upper()} Images ({len(image_types[img_type])}):")
        print("-" * 40)
        
        # Sort by timestamp (newest first)
        sorted_images = sorted(image_types[img_type], key=lambda x: x['timestamp'], reverse=True)
        
        for img in sorted_images:
            print(f"   📄 {img['filename']}")
            print(f"      Size: {img['size_mb']:.2f} MB")
            print(f"      Time: {img['timestamp']}")
            print(f"      Path: {img['path']}")
            print()
    
    # Show total stats
    total_images = len(image_files)
    total_size = sum(os.path.getsize(f) for f in image_files) / (1024 * 1024)
    
    print("=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   Total Images: {total_images}")
    print(f"   Total Size: {total_size:.2f} MB")
    print(f"   Images Directory: {images_dir}")
    
    # Show how to open images
    print(f"\n💡 To view images:")
    print(f"   - On macOS: open {images_dir}")
    print(f"   - On Windows: explorer {images_dir}")
    print(f"   - On Linux: xdg-open {images_dir}")

def open_images_folder():
    """Open the images folder in the default file manager"""
    import platform
    import subprocess
    
    images_dir = os.path.join(os.path.dirname(__file__), "images")
    
    if not os.path.exists(images_dir):
        print("❌ Images directory not found!")
        return
    
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", images_dir])
        elif system == "Windows":
            subprocess.run(["explorer", images_dir])
        elif system == "Linux":
            subprocess.run(["xdg-open", images_dir])
        else:
            print(f"❌ Unsupported operating system: {system}")
            return
        
        print(f"✅ Opened images folder: {images_dir}")
    except Exception as e:
        print(f"❌ Error opening folder: {str(e)}")

if __name__ == "__main__":
    print("🛰️ Satellite Images Viewer")
    print("=" * 60)
    
    # List all images
    list_images()
    
    print(f"\n🚀 Actions:")
    print("   1. List images (current)")
    print("   2. Open images folder")
    
    try:
        choice = input("\nEnter choice (1 or 2, or press Enter to exit): ").strip()
        
        if choice == "2":
            open_images_folder()
        elif choice == "1":
            pass  # Already listed
        else:
            print("👋 Goodbye!")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
