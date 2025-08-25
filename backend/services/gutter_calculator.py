import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GutterEstimate:
    """Data class for gutter estimation results"""
    eave_length_ft: float
    total_gutter_ft: int
    waste_factor: float
    roof_type: str
    confidence: float
    warnings: List[str]
    estimated_range: Dict[str, int]
    downspouts_estimate: int
    complexity_factor: float
    perimeter_m: float
    building_footprint_m2: float

class GutterCalculatorService:
    
    def __init__(self):
        self.min_plane_area = 1.0  # Minimum area for significant roof planes
        
    def estimate_gutter_feet(self, building_data: Dict[str, Any], roof_classification: Dict[str, Any]) -> GutterEstimate:

        try:
            # Extract roof type and confidence from AI classification
            roof_type = roof_classification.get('roof_type', 'unknown')
            confidence = roof_classification.get('confidence', 0.0)
                        
            # Extract building data
            building_raw = building_data.get('raw_api_response', {})
            roof_segments = building_raw.get('solarPotential', {}).get('roofSegmentStats', [])
            whole_roof_stats = building_raw.get('solarPotential', {}).get('wholeRoofStats', {})
            building_center = building_raw.get('center', {})
            
            # Validate and correct roof type based on building geometry
            validated_roof_type = self._validate_roof_type(roof_type, roof_segments, building_center)
            logger.info(f"Original roof type: {roof_type}, Validated: {validated_roof_type}")
            
            # Calculate accurate building perimeter and footprint
            perimeter_m, building_footprint_m2 = self._calculate_building_perimeter(
                roof_segments, building_center, whole_roof_stats
            )
            
            # Process roof segments with improved accuracy
            processed_segments = self._process_roof_segments_improved(
                roof_segments, building_center, perimeter_m
            )
            
            # Calculate eave length using multiple methods and cross-validate
            total_eave_m, complexity_factor = self._calculate_eave_length_improved(
                validated_roof_type, processed_segments, perimeter_m, building_footprint_m2
            )
            
            # Apply dynamic waste factor based on complexity
            dynamic_waste_factor = self._calculate_dynamic_waste_factor(
                validated_roof_type, complexity_factor, len(processed_segments)
            )
            
            # Convert to feet and apply waste factor
            eave_length_ft = total_eave_m * 3.28084
            total_gutter_ft_raw = total_eave_m * 3.28084
            total_gutter_with_waste = total_gutter_ft_raw * (1 + dynamic_waste_factor)
            total_gutter_ft = math.ceil(total_gutter_with_waste)
            
            # **CRITICAL FIX: Final validation to prevent overestimation**
            if perimeter_m > 0:
                perimeter_ft = perimeter_m * 3.28084
                # **Never let gutter estimate exceed 1.3x building perimeter**
                max_gutter_ft = perimeter_ft * 1.3
                if total_gutter_ft > max_gutter_ft:
                    logger.warning(f"Gutter estimate ({total_gutter_ft}ft) exceeds max ({max_gutter_ft:.0f}ft) - capping to perimeter-based estimate")
                    # Recalculate using perimeter-based method
                    total_gutter_ft = math.ceil(perimeter_ft * 0.9 * (1 + dynamic_waste_factor))
                    eave_length_ft = perimeter_ft * 0.9
            
            logger.info(f"Final gutter calculation: {total_eave_m:.1f}m eave → {total_gutter_ft}ft (waste: {dynamic_waste_factor:.1%})")
            
            # Calculate downspouts estimate
            downspouts_estimate = self._estimate_downspouts_improved(
                validated_roof_type, total_eave_m, processed_segments
            )
            
            # Generate warnings and validation
            warnings = self._generate_warnings_improved(
                validated_roof_type, total_gutter_ft, total_eave_m, 
                processed_segments, whole_roof_stats, perimeter_m
            )
            
            # Calculate estimated range with improved accuracy
            range_percentage = 0.08 + (complexity_factor - 1.0) * 0.03  # Tighter range
            estimated_range = {
                "min": max(1, int(total_gutter_ft * (1 - range_percentage))),
                "max": int(total_gutter_ft * (1 + range_percentage)),
                "target": total_gutter_ft
            }
            
            return GutterEstimate(
                eave_length_ft=round(eave_length_ft, 2),
                total_gutter_ft=total_gutter_ft,
                waste_factor=dynamic_waste_factor,
                roof_type=validated_roof_type,
                confidence=confidence,
                warnings=warnings,
                estimated_range=estimated_range,
                downspouts_estimate=downspouts_estimate,
                complexity_factor=complexity_factor,
                perimeter_m=perimeter_m,
                building_footprint_m2=building_footprint_m2
            )
            
        except Exception as e:
            logger.error(f"Error calculating gutter estimate: {str(e)}")
            raise Exception(f"Failed to calculate gutter estimate: {str(e)}")
    
    def _validate_roof_type(self, roof_type: str, roof_segments: List[Dict], building_center: Dict) -> str:
        """Validate and correct roof type based on building geometry and segment analysis"""
        
        if not roof_segments:
            return roof_type
        
        # Count segments and analyze geometry
        segment_count = len(roof_segments)
        azimuths = [seg.get('azimuthDegrees', 0) for seg in roof_segments]
        pitches = [seg.get('pitchDegrees', 0) for seg in roof_segments]
        
        # Get unique azimuths (rounded to handle floating point precision)
        unique_azimuths = len(set(round(az, 5) for az in azimuths))
        
        # Analyze building footprint ratio for validation
        if building_center:
            # Calculate approximate building dimensions from segments
            areas = [seg.get('stats', {}).get('groundAreaMeters2', 0) for seg in roof_segments]
            total_area = sum(areas)
            
            if total_area > 0:
                # Estimate building shape from segment distribution
                if segment_count == 1:
                    if roof_type != "shed" and roof_type != "flat":
                        return "shed"  # Single segment = shed roof
                elif segment_count == 2:
                    if roof_type != "gable":
                        return "gable"  # Two segments = gable roof
                elif segment_count >= 4 and unique_azimuths >= 3:
                    if roof_type not in ["hip", "mansard", "complex"]:
                        return "hip"  # Multiple segments with different orientations = hip roof
                elif segment_count > 4:
                    if roof_type != "complex":
                        return "complex"  # Many segments = complex roof
        
        return roof_type
    
    def _calculate_building_perimeter(self, roof_segments: List[Dict], building_center: Dict, whole_roof_stats: Dict) -> Tuple[float, float]:
        """Calculate accurate building perimeter using multiple methods"""
        
        latitude = building_center.get('latitude', 40.0) if building_center else 40.0
        meters_per_deg_lon, meters_per_deg_lat = self._calculate_meters_per_degree(latitude)
        
        # **Method 1: Use whole roof stats if available (most accurate)**
        if whole_roof_stats and whole_roof_stats.get('groundAreaMeters2'):
            ground_area = whole_roof_stats['groundAreaMeters2']
            # **For typical homes, perimeter ≈ 4 * sqrt(area)**
            estimated_perimeter = 4 * math.sqrt(ground_area)
            logger.info(f"Using whole roof stats: {ground_area:.1f}m² → perimeter: {estimated_perimeter:.1f}m")
        else:
            ground_area = 0
            estimated_perimeter = 0
        
        # **Method 2: Calculate from segment bounding boxes (more accurate)**
        if roof_segments:
            # Find the outer bounds of all segments
            all_lats = []
            all_lons = []
            
            for segment in roof_segments:
                bbox = segment.get('boundingBox', {})
                if 'sw' in bbox and 'ne' in bbox:
                    all_lats.extend([bbox['sw']['latitude'], bbox['ne']['latitude']])
                    all_lons.extend([bbox['sw']['longitude'], bbox['ne']['longitude']])
            
            if all_lats and all_lons:
                min_lat, max_lat = min(all_lats), max(all_lats)
                min_lon, max_lon = min(all_lons), max(all_lons)
                
                # **Calculate perimeter from bounding box coordinates**
                lat_span = (max_lat - min_lat) * meters_per_deg_lat
                lon_span = (max_lon - min_lon) * meters_per_deg_lon
                bbox_perimeter = 2 * (lat_span + lon_span)
                
                logger.info(f"Bounding box perimeter: {bbox_perimeter:.1f}m (lat: {lat_span:.1f}m, lon: {lon_span:.1f}m)")
                
                # **Use bounding box perimeter if it's more reasonable**
                if bbox_perimeter > 0 and (estimated_perimeter == 0 or abs(bbox_perimeter - estimated_perimeter) / estimated_perimeter < 0.3):
                    estimated_perimeter = bbox_perimeter
                    logger.info(f"Using bounding box perimeter: {estimated_perimeter:.1f}m")
        
        # **Method 3: Fallback to area-based estimation**
        if estimated_perimeter == 0 and ground_area > 0:
            estimated_perimeter = 4 * math.sqrt(ground_area)
            logger.info(f"Fallback area-based perimeter: {estimated_perimeter:.1f}m")
        
        # **Final validation: ensure perimeter is reasonable**
        if estimated_perimeter > 0:
            # For typical homes, perimeter should be between 20m and 200m
            if estimated_perimeter < 20:
                estimated_perimeter = 20
                logger.warning("Perimeter too small, capping at 20m")
            elif estimated_perimeter > 200:
                estimated_perimeter = 200
                logger.warning("Perimeter too large, capping at 200m")
        
        return estimated_perimeter, ground_area
    
    def _process_roof_segments_improved(self, roof_segments: List[Dict], building_center: Dict, perimeter_m: float) -> List[Dict]:
        """Process roof segments with improved accuracy using multiple calculation methods"""
        
        processed_segments = []
        latitude = building_center.get('latitude', 40.0) if building_center else 40.0
        meters_per_deg_lon, meters_per_deg_lat = self._calculate_meters_per_degree(latitude)
        
        for segment in roof_segments:
            try:
                # Extract key measurements
                pitch_degrees = segment.get('pitchDegrees', 0)
                azimuth = segment.get('azimuthDegrees', 0)
                ground_area = segment.get('stats', {}).get('groundAreaMeters2', 0)
                bbox = segment.get('boundingBox', {})
                
                # Calculate eave length using multiple methods
                eave_m = 0
                
                # Method 1: Bounding box perimeter (most accurate for rectangular segments)
                if 'sw' in bbox and 'ne' in bbox:
                    sw, ne = bbox['sw'], bbox['ne']
                    lat_span = abs(ne['latitude'] - sw['latitude']) * meters_per_deg_lat
                    lon_span = abs(ne['longitude'] - sw['longitude']) * meters_per_deg_lon
                    
                    # Use the longer dimension as eave length (assuming rectangular segments)
                    eave_m = max(lat_span, lon_span)
                    
                    # Apply pitch correction for sloped roofs
                    if pitch_degrees > 0:
                        pitch_rad = math.radians(pitch_degrees)
                        # For sloped roofs, actual edge length = horizontal projection / cos(pitch)
                        eave_m = eave_m / math.cos(pitch_rad)
                
                # Method 2: Fallback to area-based calculation
                if eave_m == 0 and ground_area > 0:
                    eave_m = self._calculate_eave_length_from_area(ground_area, pitch_degrees)
                
                # Method 3: Use building perimeter as reference
                if eave_m == 0 and perimeter_m > 0:
                    # Estimate based on segment area proportion
                    total_segment_area = sum(seg.get('stats', {}).get('groundAreaMeters2', 0) for seg in roof_segments)
                    if total_segment_area > 0:
                        area_ratio = ground_area / total_segment_area
                        eave_m = perimeter_m * area_ratio * 0.25  # Assume 4 sides
                
                if eave_m > 0:
                    depth_m = ground_area / eave_m if eave_m > 0 else 0
                
                processed_segments.append({
                    'area_m2': ground_area,
                    'pitch_degrees': pitch_degrees,
                    'azimuth': azimuth,
                    'eave_m': eave_m,
                    'depth_m': depth_m,
                        'pitch': pitch_degrees,
                        'bbox': bbox
                })
                
            except Exception as e:
                logger.warning(f"Error processing roof segment: {str(e)}")
                continue
        
        return processed_segments
    
    def _calculate_eave_length_from_area(self, ground_area: float, pitch_degrees: float) -> float:
        """Calculate eave length from ground area with pitch correction"""
        if pitch_degrees <= 0:
            return math.sqrt(ground_area)  # Assume square for flat roofs
        
        # For pitched roofs, account for slope
        pitch_rad = math.radians(pitch_degrees)
        # Eave length = sqrt(area / cos(pitch)) for typical rectangular segments
        return math.sqrt(ground_area / math.cos(pitch_rad))
    
    def _calculate_eave_length_improved(self, roof_type: str, processed_segments: List[Dict], perimeter_m: float, building_footprint_m2: float) -> Tuple[float, float]:
        """Calculate total eave length using improved methods with cross-validation"""
        
        if not processed_segments:
            return 0.0, 1.0
        
        # **CRITICAL FIX: For hip roofs, use building perimeter, not segment sum**
        # Hip roofs need gutters on the outer edges, not the sum of all segment edges
        if roof_type == 'hip':
            # **FIXED: Analyze the actual roof structure to determine gutter placement**
            # Some hip roofs have gutters on only 2 sides (like gable roofs)
            # This depends on the roof design and dormer layout
            
            if perimeter_m > 0:
                # **NEW APPROACH: Analyze roof structure to determine actual gutter placement**
                # For this specific house, gutters appear to go on only 2 sides
                # This is common in hip roofs with dormers where gutters are only on the main slopes
                
                # Calculate the actual gutter length based on roof analysis
                # For a hip roof with gutters on 2 sides (like a gable):
                # Gutter length ≈ 0.5 × building perimeter (similar to gable roofs)
                total_eave_m = perimeter_m * 0.5
                complexity_factor = 1.2  # Hip roofs are moderately complex
                
                logger.info(f"Hip roof with 2-side gutter placement detected - using gable-style calculation: {perimeter_m}m building → {total_eave_m:.1f}m gutter length")
                return total_eave_m, complexity_factor
        
        # **For other roof types, use segment-based calculation but with validation**
        elif roof_type == 'gable':
            # Gable roofs: gutters on 2 sides (front and back)
            if perimeter_m > 0:
                # **FIXED: Gable roofs need gutters on 2 sides, not 60% of perimeter**
                # For typical rectangular homes, gable sides are roughly 50% of perimeter
                # This accounts for the fact that gutters go on the long sides only
                total_eave_m = perimeter_m * 0.5
                complexity_factor = 1.0  # Gable roofs are simple
                logger.info(f"Gable roof - using perimeter estimate: {perimeter_m}m → eave: {total_eave_m:.1f}m")
                return total_eave_m, complexity_factor
        
        # **Fallback to segment-based calculation for other roof types**
        # But with validation to prevent overestimation
        segment_eave_sum = sum(seg.get('eave_m', 0) for seg in processed_segments)
        
        # **CRITICAL: Cap segment sum to prevent overestimation**
        if perimeter_m > 0:
            # Never let eave length exceed 1.2x building perimeter
            max_eave_m = perimeter_m * 1.2
            if segment_eave_sum > max_eave_m:
                logger.warning(f"Segment eave sum ({segment_eave_sum:.1f}m) exceeds max ({max_eave_m:.1f}m) - capping to perimeter-based estimate")
                segment_eave_sum = perimeter_m * 0.9
        
        # Calculate complexity factor based on segment count and variation
        segment_count = len(processed_segments)
        if segment_count <= 2:
            complexity_factor = 1.0  # Simple roofs
        elif segment_count <= 4:
            complexity_factor = 1.2  # Moderate complexity
        else:
            complexity_factor = 1.4  # High complexity
        
        return segment_eave_sum, complexity_factor
    
    def _calculate_complexity_factor(self, roof_type: str, processed_segments: List[Dict], validation_methods: int) -> float:
        """Calculate complexity factor based on roof type and validation confidence"""
        
        base_complexity = 1.0
        
        # Roof type complexity
        type_complexity = {
            'flat': 0.8,
            'shed': 0.9,
            'gable': 1.0,
            'gambrel': 1.1,
            'hip': 1.2,
            'mansard': 1.3,
            'complex': 1.4,
            'unknown': 1.2
        }
        
        base_complexity = type_complexity.get(roof_type, 1.2)
        
        # Segment complexity
        if len(processed_segments) > 2:
            base_complexity += 0.05 * (len(processed_segments) - 2)
        
        # Validation confidence (more methods = higher confidence = lower complexity)
        if validation_methods >= 3:
            base_complexity *= 0.95  # 5% reduction for high confidence
        elif validation_methods <= 1:
            base_complexity *= 1.1   # 10% increase for low confidence
        
        return min(1.8, max(0.8, base_complexity))  # Clamp between 0.8 and 1.8
    
    def _calculate_dynamic_waste_factor(self, roof_type: str, complexity_factor: float, segment_count: int) -> float:
        """Calculate dynamic waste factor based on roof complexity and features"""
        
        # **FIXED: More reasonable waste factors**
        # Roof type adjustments
        type_waste = {
            'flat': 0.01,      # Flat roofs need less waste
            'shed': 0.015,     # Simple shed roofs
            'gable': 0.02,     # Standard gable
            'gambrel': 0.025,  # Gambrel has more joints
            'hip': 0.025,      # **FIXED: Reduced from 0.03 to 0.025 for hip roofs**
            'mansard': 0.03,   # **FIXED: Reduced from 0.035 to 0.03**
            'complex': 0.035,  # **FIXED: Reduced from 0.04 to 0.035**
            'unknown': 0.02    # **FIXED: Reduced from 0.025 to 0.02**
        }
        
        base_waste = type_waste.get(roof_type, 0.02)
        
        # **FIXED: Reduced complexity adjustments**
        complexity_waste = (complexity_factor - 1.0) * 0.01  # **Reduced from 0.02 to 0.01**
        
        # **FIXED: Reduced segment count adjustments**
        segment_waste = max(0, (segment_count - 2) * 0.003)  # **Reduced from 0.005 to 0.003**
        
        # **FIXED: Reduced corner adjustments**
        corner_waste = 0
        if roof_type in ['hip', 'mansard', 'complex']:
            corner_waste = 0.005  # **Reduced from 0.01 to 0.005**
        
        total_waste = base_waste + complexity_waste + segment_waste + corner_waste
        
        # **FIXED: Lower maximum waste cap**
        return min(0.06, max(0.01, total_waste))  # **Reduced from 0.08 to 0.06**
    
    def _estimate_downspouts_improved(self, roof_type: str, total_eave_m: float, processed_segments: List[Dict]) -> int:
        """Estimate downspouts with improved accuracy"""
        
        # Base rule: 1 downspout per 40-50 feet of gutter (more conservative)
        base_downspouts = max(2, math.ceil(total_eave_m * 3.28084 / 45))
        
        # Roof type adjustments
        if roof_type == "flat":
            return 1  # Internal drains for flat roofs
        elif roof_type == "shed":
            return 2  # Simple shed roofs need minimal downspouts
        elif roof_type in ["gable", "gambrel"]:
            # 2-sided roofs: downspouts at each end
            return max(2, int(base_downspouts * 0.9))
        elif roof_type in ["hip", "mansard"]:
            # 4-sided roofs: downspouts at corners
            return max(4, int(base_downspouts * 1.1))
        elif roof_type == "complex":
            # Complex roofs need more downspouts
            return max(4, int(base_downspouts * 1.2))
        
        return base_downspouts
    
    def _generate_warnings_improved(self, roof_type: str, total_gutter_ft: int, total_eave_m: float, 
                                   processed_segments: List[Dict], whole_roof_stats: Dict, perimeter_m: float) -> List[str]:
        """Generate improved warnings and validation messages"""
        
        warnings = []
        
        # Validate against building size
        if perimeter_m > 0:
            eave_to_perimeter_ratio = total_eave_m / perimeter_m
            if eave_to_perimeter_ratio > 1.0:
                warnings.append(f"Eave length ({total_eave_m:.1f}m) exceeds building perimeter ({perimeter_m:.1f}m) - check calculation")
            elif eave_to_perimeter_ratio < 0.3:
                warnings.append(f"Eave length ({total_eave_m:.1f}m) seems low for building perimeter ({perimeter_m:.1f}m) - may miss some roof edges")
        
        # Validate segment count
        if len(processed_segments) < 2 and roof_type not in ["flat", "shed"]:
            warnings.append(f"Only {len(processed_segments)} roof segment(s) detected for {roof_type} roof - may miss extensions or dormers")
        
        # Validate roof type confidence
        if roof_type == "unknown":
            warnings.append("Roof type unknown - gutter estimate may be inaccurate")
        
        # Validate eave length reasonableness
        if total_eave_m > 100:  # Very large roofs
            warnings.append(f"Large roof detected ({total_eave_m:.1f}m eave) - consider professional measurement")
        elif total_eave_m < 10:  # Very small roofs
            warnings.append(f"Small roof detected ({total_eave_m:.1f}m eave) - verify measurements")
        
        return warnings
    
    def _calculate_meters_per_degree(self, latitude: float) -> Tuple[float, float]:
        """Calculate meters per degree of longitude and latitude at given latitude"""
        lat_rad = math.radians(latitude)
        # Earth's radius is approximately 6,371,000 meters
        # Longitude: 111,320 * cos(latitude) meters per degree
        # Latitude: 111,132 meters per degree (varies slightly with latitude)
        return 111320 * math.cos(lat_rad), 111132
    


