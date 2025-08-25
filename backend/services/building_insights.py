import aiohttp
from typing import Dict, Any
from config import config
from services.geocode import geocode_address

class BuildingInsightsService:
    def __init__(self):
        self.api_key = config.google_api_key
        
        if not self.api_key:
            raise Exception("Google Maps API key is required")
    
    async def get_building_insights(self, address: str) -> Dict[str, Any]:
        """
        Get building insights from Google Solar API using:
        https://solar.googleapis.com/v1/buildingInsights:findClosest
        
        Accepts address and geocodes it internally
        """
        try:
            # First geocode the address
            lat, lng = geocode_address(address)
            if not lat or not lng:
                raise Exception(f"Failed to geocode address: {address}")
            
            print(f"Geocoded address '{address}' to coordinates: {lat}, {lng}")
            
            async with aiohttp.ClientSession() as session:
                building_url = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
                building_params = {
                    "location.latitude": lat,
                    "location.longitude": lng,
                    "key": self.api_key
                }
                
                async with session.get(building_url, params=building_params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Building insights API error: {response.status}, {error_text}")
                    
                    building_data = await response.json()
                
                # Return raw data + geocoded coordinates
                return {
                    "raw_api_response": building_data,
                    "geocoded_coordinates": {
                        "latitude": lat,
                        "longitude": lng
                    },
                    "address": address
                }
                
        except Exception as e:
            print(f"Building insights API failed: {e}")
            raise Exception(f"Building insights API failed: {str(e)}")
