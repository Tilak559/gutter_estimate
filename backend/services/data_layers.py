import aiohttp
from typing import Dict, Any
from config import config
from services.geocode import geocode_address

class DataLayersService:
    def __init__(self):
        self.api_key = config.google_api_key
        
        if not self.api_key:
            raise Exception("Google Maps API key is required")
    
    async def get_data_layers(self, address: str) -> Dict[str, Any]:
        """
        Get data layers from Google Solar API using:
        https://solar.googleapis.com/v1/dataLayers:get
        
        Accepts address and geocodes it internally.
        Uses 15m radius for precise house coverage.
        """
        try:
            # First geocode the address
            lat, lng = geocode_address(address)
            if not lat or not lng:
                raise Exception(f"Failed to geocode address: {address}")
            
            print(f"Geocoded address '{address}' to coordinates: {lat}, {lng}")
            
            async with aiohttp.ClientSession() as session:
                # Use the correct Google Solar API endpoint
                data_layers_url = "https://solar.googleapis.com/v1/dataLayers:get"
                data_layers_params = {
                    "location.latitude": lat,
                    "location.longitude": lng,
                    "radiusMeters": 15,  # Set to 15m for precise house coverage
                    "view": "FULL_LAYERS",
                    "key": self.api_key
                }
                
                print(f"=== DATA LAYERS API CALL ===")
                print(f"URL: {data_layers_url}")
                print(f"Params: {data_layers_params}")
                print(f"API Key: {self.api_key[:10]}...{self.api_key[-10:] if len(self.api_key) > 20 else '***'}")
                
                async with session.get(data_layers_url, params=data_layers_params) as response:
                    print(f"Response status: {response.status}")
                    print(f"Response headers: {dict(response.headers)}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ Data layers API error: {response.status}")
                        print(f"Error response: {error_text}")
                        
                        # Check if it's an API key issue
                        if "API key not valid" in error_text or "quota" in error_text.lower():
                            print("🔑 This appears to be an API key or quota issue")
                        elif "not found" in error_text.lower():
                            print("📍 This address may not have Solar API coverage")
                        
                        raise Exception(f"Data layers API error: {response.status}, {error_text}")
                    
                    # Success! Parse the response
                    data_layers_data = await response.json()
                    print(f"✅ Data layers API success!")
                    print(f"Response keys: {list(data_layers_data.keys())}")
                    
                    # Check if we have any imagery data
                    imagery_keys = ['imagery', 'rgb', 'dsm', 'mask', 'imageryUrl', 'rgbUrl', 'dsmUrl', 'maskUrl']
                    has_imagery = any(key in data_layers_data for key in imagery_keys)
                    print(f"Has imagery data: {has_imagery}")
                    
                    if has_imagery:
                        for key in imagery_keys:
                            if key in data_layers_data:
                                print(f"✅ Found {key} data: {data_layers_data[key]}")
                    else:
                        print("⚠️ No imagery data found in API response")
                        print("Available keys:", list(data_layers_data.keys()))
                        
                        # Show the full response structure for debugging
                        print("Full response structure:")
                        for key, value in data_layers_data.items():
                            if isinstance(value, dict):
                                print(f"  {key}: {list(value.keys())}")
                            elif isinstance(value, list):
                                print(f"  {key}: [{len(value)} items]")
                            else:
                                print(f"  {key}: {str(value)[:100]}...")
                
                # Return raw data + geocoded coordinates
                return {
                    "raw_api_response": data_layers_data,
                    "geocoded_coordinates": {
                        "latitude": lat,
                        "longitude": lng
                    },
                    "address": address
                }
                
        except Exception as e:
            print(f"❌ Data layers API failed: {e}")
            print(f"Exception type: {type(e).__name__}")
            
            # Return empty response but preserve coordinates
            return {
                "raw_api_response": {},
                "geocoded_coordinates": {
                    "latitude": lat,
                    "longitude": lng
                },
                "address": address,
                "fallback": True,
                "error": str(e)
            }
    
    def _get_fallback_image_url(self, lat: float, lng: float) -> str:
        """Get fallback satellite image URL using Google Static Maps"""
        return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=20&size=400x400&maptype=satellite&key={self.api_key}"
