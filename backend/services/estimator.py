import math
from typing import Dict, Any, List

class GutterEstimator:
    def __init__(self):
        self.downspout_ratio = 10  # 1 downspout per 10 meters of gutter
        
    def estimate_gutter(self, roof_type: str, stats: dict) -> Dict[str, Any]:
        """
        Estimate gutter length and downspouts based on roof type and statistics
        """
        segments = stats.get("segments", [])
        bounding_box = stats.get("boundingBox", {})
        
        if roof_type == "gable":
            return self._estimate_gable(segments, bounding_box)
        elif roof_type == "hip":
            return self._estimate_hip(segments, bounding_box)
        elif roof_type == "flat":
            return self._estimate_flat(segments, bounding_box)
        elif roof_type == "mansard":
            return self._estimate_mansard(segments, bounding_box)
        elif roof_type == "gambrel":
            return self._estimate_gambrel(segments, bounding_box)
        elif roof_type == "shed":
            return self._estimate_shed(segments, bounding_box)
        elif roof_type == "complex":
            return self._estimate_complex(segments, bounding_box)
        else:
            # Default to gable estimation
            return self._estimate_gable(segments, bounding_box)
    
    def _estimate_gable(self, segments: List[dict], bounding_box: dict) -> Dict[str, Any]:
        """Gable roof: gutters on two long sides"""
        if not bounding_box:
            return self._fallback_estimation(segments)
        
        # Calculate perimeter of the main rectangle
        width = self._calculate_distance(
            bounding_box.get("west", 0), bounding_box.get("east", 0)
        )
        length = self._calculate_distance(
            bounding_box.get("south", 0), bounding_box.get("north", 0)
        )
        
        # Gable roofs typically have gutters on the two long sides
        eave_length = max(width, length) * 2  # Two sides
        
        return self._finalize_estimation(eave_length, segments)
    
    def _estimate_hip(self, segments: List[dict], bounding_box: dict) -> Dict[str, Any]:
        """Hip roof: gutters on all four sides"""
        if not bounding_box:
            return self._fallback_estimation(segments)
        
        width = self._calculate_distance(
            bounding_box.get("west", 0), bounding_box.get("east", 0)
        )
        length = self._calculate_distance(
            bounding_box.get("south", 0), bounding_box.get("north", 0)
        )
        
        # Hip roofs have gutters on all four sides
        eave_length = (width + length) * 2
        
        return self._finalize_estimation(eave_length, segments)
    
    def _estimate_flat(self, segments: List[dict], bounding_box: dict) -> Dict[str, Any]:
        """Flat roof: minimal gutters, mostly internal drains"""
        if not bounding_box:
            return self._fallback_estimation(segments)
        
        width = self._calculate_distance(
            bounding_box.get("west", 0), bounding_box.get("east", 0)
        )
        length = self._calculate_distance(
            bounding_box.get("south", 0), bounding_box.get("north", 0)
        )
        
        # Flat roofs typically have minimal perimeter gutters
        eave_length = (width + length) * 2 * 0.3  # 30% of perimeter
        
        return self._finalize_estimation(eave_length, segments)
    
    def _estimate_mansard(self, segments: List[dict], bounding_box: dict) -> Dict[str, Any]:
        """Mansard roof: gutters on multiple levels"""
        if not bounding_box:
            return self._fallback_estimation(segments)
        
        width = self._calculate_distance(
            bounding_box.get("west", 0), bounding_box.get("east", 0)
        )
        length = self._calculate_distance(
            bounding_box.get("south", 0), bounding_box.get("north", 0)
        )
        
        # Mansard roofs have gutters on multiple levels
        eave_length = (width + length) * 2 * 1.5  # 1.5x perimeter for multiple levels
        
        return self._finalize_estimation(eave_length, segments)
    
    def _estimate_gambrel(self, segments: List[dict], bounding_box: dict) -> Dict[str, Any]:
        """Gambrel roof: similar to mansard but different slope pattern"""
        if not bounding_box:
            return self._fallback_estimation(segments)
        
        width = self._calculate_distance(
            bounding_box.get("west", 0), bounding_box.get("east", 0)
        )
        length = self._calculate_distance(
            bounding_box.get("south", 0), bounding_box.get("north", 0)
        )
        
        # Gambrel roofs have gutters on multiple levels
        eave_length = (width + length) * 2 * 1.4  # 1.4x perimeter
        
        return self._finalize_estimation(eave_length, segments)
    
    def _estimate_shed(self, segments: List[dict], bounding_box: dict) -> Dict[str, Any]:
        """Shed roof: gutters on one side only"""
        if not bounding_box:
            return self._fallback_estimation(segments)
        
        width = self._calculate_distance(
            bounding_box.get("west", 0), bounding_box.get("east", 0)
        )
        length = self._calculate_distance(
            bounding_box.get("south", 0), bounding_box.get("north", 0)
        )
        
        # Shed roofs typically have gutters on one long side
        eave_length = max(width, length)  # One side only
        
        return self._finalize_estimation(eave_length, segments)
    
    def _estimate_complex(self, segments: List[dict], bounding_box: dict) -> Dict[str, Any]:
        """Complex roof: use all available segments and bounding box"""
        if not bounding_box:
            return self._fallback_estimation(segments)
        
        width = self._calculate_distance(
            bounding_box.get("west", 0), bounding_box.get("east", 0)
        )
        length = self._calculate_distance(
            bounding_box.get("south", 0), bounding_box.get("north", 0)
        )
        
        # Complex roofs: use full perimeter plus segment-based adjustments
        base_perimeter = (width + length) * 2
        
        # Add complexity factor based on number of segments
        complexity_factor = 1.0 + (len(segments) - 2) * 0.1  # 10% per additional segment
        eave_length = base_perimeter * complexity_factor
        
        return self._finalize_estimation(eave_length, segments)
    
    def _fallback_estimation(self, segments: List[dict]) -> Dict[str, Any]:
        """Fallback estimation when bounding box is not available"""
        if not segments:
            return self._finalize_estimation(100.0, [])  # Default 100m
        
        # Use segment areas to estimate
        total_area = sum(seg.get("groundAreaMeters2", 0) for seg in segments)
        estimated_perimeter = math.sqrt(total_area) * 4  # Rough perimeter estimate
        
        return self._finalize_estimation(estimated_perimeter, segments)
    
    def _calculate_distance(self, coord1: float, coord2: float) -> float:
        """Calculate distance between two coordinates (simplified)"""
        return abs(coord1 - coord2) * 111000  # Rough conversion to meters
    
    def _finalize_estimation(self, eave_length: float, segments: List[dict]) -> Dict[str, Any]:
        """Finalize the estimation with downspouts and range"""
        # Convert to meters if needed
        if eave_length > 1000:  # Likely in degrees, convert to meters
            eave_length = eave_length / 111000
        
        # Calculate downspouts
        downspouts = max(2, round(eave_length / self.downspout_ratio))
        
        # Calculate range (±10%)
        range_buffer = eave_length * 0.1
        range_m = [eave_length - range_buffer, eave_length + range_buffer]
        
        return {
            "eave_length_m": round(eave_length, 1),
            "downspouts": downspouts,
            "range_m": [round(r, 1) for r in range_m]
        }
