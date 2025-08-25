import math
from typing import Tuple, Dict, Any

def lat_lng_to_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two lat/lng points in meters using Haversine formula
    """
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def bounding_box_to_dimensions(bounding_box: Dict[str, float]) -> Tuple[float, float]:
    """
    Convert bounding box coordinates to width and length in meters
    """
    if not bounding_box:
        return 0.0, 0.0
    
    north = bounding_box.get("north", 0)
    south = bounding_box.get("south", 0)
    east = bounding_box.get("east", 0)
    west = bounding_box.get("west", 0)
    
    # Calculate center point for more accurate distance calculation
    center_lat = (north + south) / 2
    
    # Convert to meters
    width = lat_lng_to_meters(center_lat, west, center_lat, east)
    length = lat_lng_to_meters(south, center_lat, north, center_lat)
    
    return width, length

def calculate_roof_area(segments: list) -> float:
    """
    Calculate total roof area from segments
    """
    if not segments:
        return 0.0
    
    total_area = sum(seg.get("roofAreaMeters2", 0) for seg in segments)
    return total_area

def calculate_average_pitch(segments: list) -> float:
    """
    Calculate average pitch from segments
    """
    if not segments:
        return 0.0
    
    pitches = [seg.get("pitchDegrees", 0) for seg in segments]
    return sum(pitches) / len(pitches)

def format_measurement(value: float, unit: str = "m") -> str:
    """
    Format measurement values with appropriate precision
    """
    if value < 1:
        return f"{value * 100:.0f}cm"
    elif value < 1000:
        return f"{value:.1f}{unit}"
    else:
        return f"{value / 1000:.2f}km"

def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Validate latitude and longitude coordinates
    """
    return -90 <= lat <= 90 and -180 <= lng <= 180

def meters_to_feet(meters: float) -> float:
    """
    Convert meters to feet
    """
    return meters * 3.28084

def feet_to_meters(feet: float) -> float:
    """
    Convert feet to meters
    """
    return feet * 0.3048
