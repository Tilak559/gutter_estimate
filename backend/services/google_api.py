import aiohttp
import asyncio
from typing import Tuple, Dict, Any
import json
from config import config

class GoogleAPIService:
    def __init__(self):
        self.api_key = config.google_api_key
        
        if not self.api_key:
            raise Exception("Google Maps API key is required")
    
    async def geocode_address(self, address: str) -> Tuple[float, float]:
        """Geocode address to lat/lng using Google Maps API"""
        async with aiohttp.ClientSession() as session:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": address,
                "key": self.api_key
            }
            
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if data["status"] != "OK":
                    raise Exception(f"Geocoding failed: {data['status']}")
                
                location = data["results"][0]["geometry"]["location"]
                return location["lat"], location["lng"]
    
    async def get_solar_data(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        Get building insights and data layers from Google Solar API
        This uses the REST API endpoints:
        - buildingInsights:findClosest for building data
        - dataLayers for satellite imagery
        """
        try:
            # Try to use real Solar API
            return await self._get_real_solar_data(lat, lng)
                
        except Exception as e:
            print(f"Google Solar API call failed: {e}")
            # Fallback to simplified approach
            return await self._get_simplified_solar_data(lat, lng)
    
    async def _get_real_solar_data(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        Get real data from Google Solar API using REST endpoints:
        - https://solar.googleapis.com/v1/buildingInsights:findClosest
        - https://solar.googleapis.com/v1/dataLayers:...
        """
        try:
            async with aiohttp.ClientSession() as session:
                
                # 1. Get building insights
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
                
                # Extract building insights data
                building_stats = building_data.get("buildingStats", {})
                segments = []
                
                for segment in building_stats.get("segments", []):
                    ground_center = segment.get("groundCenter", {})
                    ground_stats = segment.get("groundStats", {})
                    roof_stats = segment.get("roofStats", {})
                    
                    segments.append({
                        "pitchDegrees": ground_center.get("pitchDegrees", 0),
                        "azimuthDegrees": ground_center.get("azimuthDegrees", 0),
                        "groundAreaMeters2": ground_stats.get("areaMeters2", 0),
                        "roofAreaMeters2": roof_stats.get("areaMeters2", 0),
                        "heightMeters": ground_stats.get("heightMeters", 0)
                    })
                
                # Get bounding box
                bounding_box_data = building_data.get("boundingBox", {})
                bounding_box = {
                    "north": bounding_box_data.get("northeast", {}).get("latitude", lat + 0.001),
                    "south": bounding_box_data.get("southwest", {}).get("latitude", lat - 0.001),
                    "east": bounding_box_data.get("northeast", {}).get("longitude", lng + 0.001),
                    "west": bounding_box_data.get("southwest", {}).get("longitude", lng - 0.001)
                }
                
                # 2. Get data layers for satellite imagery
                data_layers_url = "https://solar.googleapis.com/v1/dataLayers:get"
                data_layers_params = {
                    "location.latitude": lat,
                    "location.longitude": lng,
                    "radiusMeters": 100,
                    "view": "FULL_LAYERS",
                    "key": self.api_key
                }
                
                async with session.get(data_layers_url, params=data_layers_params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Data layers API error: {response.status}, {error_text}")
                        # Continue without data layers, use fallback
                        image_url = self._get_fallback_image_url(lat, lng)
                    else:
                        data_layers_data = await response.json()
                        # Extract satellite imagery from data layers
                        image_url = self._extract_satellite_image_from_datalayers(data_layers_data, lat, lng)
                
                return {
                    "building_insights": {
                        "segments": segments,
                        "boundingBox": bounding_box,
                        "totalGroundAreaMeters2": building_stats.get("groundAreaMeters2", 0),
                        "totalRoofAreaMeters2": building_stats.get("roofAreaMeters2", 0)
                    },
                    "image_url": image_url
                }
                
        except Exception as e:
            print(f"Real Solar API failed: {e}")
            raise Exception(f"Real Solar API failed: {str(e)}")
    
    def _extract_satellite_image_from_datalayers(self, data_layers_data: dict, lat: float, lng: float) -> str:
        """
        Extract satellite imagery from Google Solar API dataLayers response
        This is the proper way to get satellite images from the Solar API
        """
        try:
            # Check if we have imagery data in the response
            imagery_data = data_layers_data.get("imagery")
            if imagery_data and "url" in imagery_data:
                print(f"Using real satellite imagery from Solar API: {imagery_data['url']}")
                return imagery_data["url"]
            
            # If no imagery in dataLayers, try other data sources
            rgb_data = data_layers_data.get("rgb")
            if rgb_data and "url" in rgb_data:
                print(f"Using RGB data from Solar API: {rgb_data['url']}")
                return rgb_data["url"]
            
            # Fallback to Google Static Maps if no Solar API imagery
            print("No imagery found in dataLayers, using Google Static Maps fallback")
            return self._get_fallback_image_url(lat, lng)
            
        except Exception as e:
            print(f"Error extracting satellite image from dataLayers: {e}")
            # Final fallback
            return self._get_fallback_image_url(lat, lng)
    
    def _get_fallback_image_url(self, lat: float, lng: float) -> str:
        """Get fallback satellite image URL using Google Static Maps"""
        return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=20&size=400x400&maptype=satellite&key={self.api_key}"
    
    async def _get_simplified_solar_data(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        Simplified approach when Solar API is not available
        Uses estimated data and Google Static Maps
        """
        # Create a bounding box around the location
        bounding_box = {
            "north": lat + 0.001,
            "south": lat - 0.001,
            "east": lng + 0.001,
            "west": lng - 0.001
        }
        
        # Estimate building dimensions
        estimated_width = 0.002 * 111000  # Convert degrees to meters
        estimated_length = 0.0015 * 111000
        
        # Create estimated segments
        segments = [
            {
                "pitchDegrees": 25.0,
                "azimuthDegrees": 180.0,
                "groundAreaMeters2": estimated_width * estimated_length * 0.5,
                "roofAreaMeters2": estimated_width * estimated_length * 0.55,
                "heightMeters": 3.0
            },
            {
                "pitchDegrees": 25.0,
                "azimuthDegrees": 0.0,
                "groundAreaMeters2": estimated_width * estimated_length * 0.5,
                "roofAreaMeters2": estimated_width * estimated_length * 0.55,
                "heightMeters": 3.0
            }
        ]
        
        # Use Google Static Maps as fallback
        image_url = self._get_fallback_image_url(lat, lng)
        
        return {
            "building_insights": {
                "segments": segments,
                "boundingBox": bounding_box,
                "totalGroundAreaMeters2": estimated_width * estimated_length,
                "totalRoofAreaMeters2": estimated_width * estimated_length * 1.1
            },
            "image_url": image_url
        }
