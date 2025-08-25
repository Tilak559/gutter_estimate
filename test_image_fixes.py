#!/usr/bin/env python3
"""
Test script for the improved image handling
"""

import requests
import json

def test_image_endpoints():
    """Test the image-related endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("=== TESTING IMAGE ENDPOINTS ===")
    
    # Test debug images endpoint
    try:
        response = requests.get(f"{base_url}/api/debug/images")
        print(f"Debug images endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Images directory: {data.get('images_directory')}")
            print(f"Total images: {data.get('total_images')}")
            if data.get('images'):
                for img in data['images']:
                    print(f"  - {img['filename']} ({img['size_mb']} MB)")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing debug endpoint: {e}")
    
    print("\n=== TESTING IMAGE SERVING ===")
    
    # Test image serving (try to get a fallback image)
    try:
        # First check what images are available
        debug_response = requests.get(f"{base_url}/api/debug/images")
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            if debug_data.get('images'):
                # Try to serve the first available image
                first_image = debug_data['images'][0]['filename']
                print(f"Testing image serving with: {first_image}")
                
                img_response = requests.get(f"{base_url}/api/images/{first_image}")
                print(f"Image serving: {img_response.status_code}")
                if img_response.status_code == 200:
                    print(f"✅ Image served successfully ({len(img_response.content)} bytes)")
                else:
                    print(f"❌ Image serving failed: {img_response.text}")
            else:
                print("No images available to test")
        else:
            print("Could not get debug info")
    except Exception as e:
        print(f"Error testing image serving: {e}")

if __name__ == "__main__":
    test_image_endpoints()
