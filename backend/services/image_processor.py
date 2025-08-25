import aiohttp
import asyncio
import os
import base64
import datetime
from typing import Dict, Any, List, Optional
from config import config
from PIL import Image
import io

class ImageProcessorService:
    def __init__(self):
        self.api_key = config.google_api_key
        
        # Create a dedicated images folder in the backend directory
        self.images_dir = os.path.join(os.path.dirname(__file__), "..", "images")
        os.makedirs(self.images_dir, exist_ok=True)
        
        if not self.api_key:
            raise Exception("Google Maps API key is required")
    
    async def download_and_process_images(self, data_layers_raw: dict) -> Dict[str, Any]:
        """
        Download satellite images from Google Solar API and prepare them for AI analysis
        """
        try:
            print(f"Starting image download and processing...")
            print(f"Data layers raw keys: {list(data_layers_raw.keys())}")
            
            # Extract image URLs from data layers
            image_urls = self._extract_image_urls(data_layers_raw)
            
            if not image_urls:
                print("No satellite images available for download")
                print(f"Available keys in data_layers_raw: {list(data_layers_raw.keys())}")
                
                # Try to create a fallback using Google Static Maps
                fallback_image = await self._create_static_maps_fallback(data_layers_raw)
                if fallback_image:
                    return {
                        "images_processed": 1,
                        "local_image_paths": [fallback_image['local_path']],
                        "base64_images": [fallback_image['base64']],
                        "image_types": ['static_maps'],
                        "images_directory": self.images_dir,
                        "fallback": True
                    }
                
                # Create a placeholder image
                fallback_image = await self._create_fallback_image()
                if fallback_image:
                    return {
                        "images_processed": 1,
                        "local_image_paths": [fallback_image['local_path']],
                        "base64_images": [fallback_image['base64']],
                        "image_types": ['fallback'],
                        "images_directory": self.images_dir,
                        "fallback": True
                    }
                
                return {
                    "images_processed": 0,
                    "local_image_paths": [],
                    "base64_images": [],
                    "error": "No images available and fallback creation failed"
                }
            
            print(f"Found {len(image_urls)} images to download:")
            for img in image_urls:
                print(f"  - {img['type']}: {img['url']}")
            
            # Download images
            downloaded_images = await self._download_images(image_urls)
            
            # Process and convert images
            processed_images = await self._process_images(downloaded_images)
            
            result = {
                "images_processed": len(processed_images),
                "local_image_paths": [img['local_path'] for img in processed_images],
                "base64_images": [img['base64'] for img in processed_images],
                "image_types": [img['type'] for img in processed_images],
                "images_directory": self.images_dir
            }
            
            print(f"Image processing result: {result}")
            return result
            
        except Exception as e:
            print(f"Image processing failed: {str(e)}")
            return {
                "images_processed": 0,
                "local_image_paths": [],
                "base64_images": [],
                "error": str(e)
            }
    
    def _extract_image_urls(self, data_layers_raw: dict) -> List[Dict[str, str]]:
        """Extract all available image URLs from data layers response"""
        image_data = []
        
        print(f"=== IMAGE EXTRACTION DEBUG ===")
        print(f"Data layers raw keys: {list(data_layers_raw.keys())}")
        
        # Check for different types of imagery - using the actual keys from Google Solar API
        imagery_keys = {
            'dsm': 'dsmUrl',
            'rgb': 'rgbUrl', 
            'mask': 'maskUrl',
            'imagery': 'imageryUrl',  # Fallback
            'rgbUrl': 'rgbUrl',       # Direct key check
            'dsmUrl': 'dsmUrl',       # Direct key check
            'maskUrl': 'maskUrl'      # Direct key check
        }
        
        # First, check for direct image URL keys
        for img_type, api_key in imagery_keys.items():
            if api_key in data_layers_raw:
                img_url = data_layers_raw[api_key]
                if img_url:  # Check if URL exists and is not empty
                    image_data.append({
                        'type': img_type,
                        'url': img_url,
                        'name': f"{img_type}_image"
                    })
                    print(f"✅ Found {img_type} image: {img_url}")
                else:
                    print(f"⚠️ Found {img_type} key but URL is empty")
            else:
                print(f"❌ No {img_type} key found")
        
        # Check for nested structures (Google API might nest image URLs)
        print(f"Checking for nested image structures...")
        for key, value in data_layers_raw.items():
            if isinstance(value, dict):
                print(f"  Checking nested dict: {key}")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str) and ('http' in sub_value or 'https' in sub_value):
                        if 'solar.googleapis.com' in sub_value or 'maps.googleapis.com' in sub_value:
                            print(f"    🔍 Found potential image URL in {key}.{sub_key}: {sub_value}")
                            # Try to determine image type from key name
                            img_type = 'unknown'
                            if 'rgb' in sub_key.lower() or 'color' in sub_key.lower():
                                img_type = 'rgb'
                            elif 'dsm' in sub_key.lower() or 'elevation' in sub_key.lower():
                                img_type = 'dsm'
                            elif 'mask' in sub_key.lower():
                                img_type = 'mask'
                            elif 'imagery' in sub_key.lower():
                                img_type = 'imagery'
                            
                            image_data.append({
                                'type': img_type,
                                'url': sub_value,
                                'name': f"{img_type}_image"
                            })
                            print(f"    ✅ Added {img_type} image from nested structure")
        
        # Also check for any URL-like strings in the response
        print(f"Searching for any URL-like strings...")
        for key, value in data_layers_raw.items():
            if isinstance(value, str) and ('http' in value or 'https' in value):
                if 'solar.googleapis.com' in value or 'maps.googleapis.com' in value:
                    print(f"🔍 Found potential image URL in {key}: {value}")
                    # Don't auto-add these, just log for debugging
        
        print(f"Total images found: {len(image_data)}")
        
        # If no images found, show the full response structure for debugging
        if not image_data:
            print(f"❌ NO IMAGES FOUND - Full response structure:")
            for key, value in data_layers_raw.items():
                if isinstance(value, dict):
                    print(f"  {key}: {list(value.keys())}")
                elif isinstance(value, list):
                    print(f"  {key}: [{len(value)} items]")
                else:
                    print(f"  {key}: {str(value)[:100]}...")
        
        return image_data
    
    async def _download_images(self, image_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Download images from URLs"""
        downloaded_images = []
        
        async with aiohttp.ClientSession() as session:
            for img_info in image_data:
                try:
                    print(f"Downloading {img_info['type']} image...")
                    
                    # Add API key to URL if it's a Google API URL
                    url = img_info['url']
                    if 'solar.googleapis.com' in url:
                        separator = '&' if '?' in url else '?'
                        url = f"{url}{separator}key={self.api_key}"
                    
                    async with session.get(url) as response:
                        print(f"Download response for {img_info['type']}: {response.status}")
                        if response.status == 200:
                            image_bytes = await response.read()
                            print(f"✅ Downloaded {img_info['type']} image ({len(image_bytes)} bytes)")
                            
                            downloaded_images.append({
                                'type': img_info['type'],
                                'name': img_info['name'],
                                'bytes': image_bytes,
                                'url': img_info['url']
                            })
                        else:
                            error_text = await response.text()
                            print(f"❌ Failed to download {img_info['type']} image: {response.status}")
                            print(f"Error response: {error_text[:200]}...")
                            
                except Exception as e:
                    print(f"❌ Error downloading {img_info['type']} image: {str(e)}")
        
        return downloaded_images
    
    async def _process_images(self, downloaded_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process downloaded images for AI analysis"""
        processed_images = []
        
        for img_info in downloaded_images:
            try:
                print(f"Processing {img_info['type']} image...")
                
                # Save image locally with descriptive name and timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{img_info['type']}_{timestamp}.png"
                local_path = os.path.join(self.images_dir, filename)
                
                # Convert to PIL Image and save
                image = Image.open(io.BytesIO(img_info['bytes']))
                image.save(local_path, 'PNG')
                
                # Convert to base64 for potential use
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # **FIXED: Add proper data URL prefix for frontend compatibility**
                img_base64_url = f"data:image/png;base64,{img_base64}"
                
                processed_images.append({
                    'type': img_info['type'],
                    'name': img_info['name'],
                    'local_path': local_path,
                    'base64': img_base64_url,  # **FIXED: Use full data URL**
                    'size': image.size,
                    'mode': image.mode
                })
                
                print(f"✅ Processed {img_info['type']} image: {local_path}")
                
            except Exception as e:
                print(f"❌ Error processing {img_info['type']} image: {str(e)}")
        
        return processed_images
    
    async def _create_fallback_image(self) -> Optional[Dict[str, Any]]:
        """Create a fallback placeholder image when no satellite images are available"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple placeholder image
            img_size = (400, 400)
            img = Image.new('RGB', img_size, color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                # Try to use a default font
                font = ImageFont.load_default()
            except:
                font = None
            
            text = "Satellite Image\nUnavailable"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (img_size[0] - text_width) // 2
            y = (img_size[1] - text_height) // 2
            
            draw.text((x, y), text, fill='#666666', font=font)
            
            # Save the fallback image
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fallback_{timestamp}.png"
            local_path = os.path.join(self.images_dir, filename)
            
            img.save(local_path, 'PNG')
            
            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # **FIXED: Add proper data URL prefix for frontend compatibility**
            img_base64_url = f"data:image/png;base64,{img_base64}"
            
            print(f"✅ Created fallback image: {local_path}")
            
            return {
                'type': 'fallback',
                'name': 'fallback_image',
                'local_path': local_path,
                'base64': img_base64_url,  # **FIXED: Use full data URL**
                'size': img_size,
                'mode': 'RGB'
            }
            
        except Exception as e:
            print(f"❌ Error creating fallback image: {str(e)}")
            return None
    
    def cleanup_temp_files(self):
        """Clean up old image files (keep last 10 images of each type)"""
        try:
            # Keep only the last 10 images of each type to avoid filling up disk
            image_types = ['dsm', 'rgb', 'mask']
            for img_type in image_types:
                # Find all files of this type
                type_files = [f for f in os.listdir(self.images_dir) if f.startswith(f"{img_type}_")]
                type_files.sort(reverse=True)  # Sort by timestamp (newest first)
                
                # Remove old files, keep only last 10
                if len(type_files) > 10:
                    for old_file in type_files[10:]:
                        old_path = os.path.join(self.images_dir, old_file)
                        os.remove(old_path)
                        print(f"Cleaned up old image: {old_file}")
        except Exception as e:
            print(f"Error cleaning up old images: {str(e)}")
    
    def get_image_for_ai(self, local_path: str) -> str:
        """Convert local image to base64 for AI analysis"""
        try:
            with open(local_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error reading image for AI: {str(e)}")
            return ""
