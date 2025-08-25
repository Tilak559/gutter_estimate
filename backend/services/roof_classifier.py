import openai
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from config import config
from services.geocode import geocode_address
from services.building_insights import BuildingInsightsService
from services.data_layers import DataLayersService
from services.image_processor import ImageProcessorService
from services.gutter_calculator import GutterCalculatorService

# Set up logging
logger = logging.getLogger(__name__)

class RoofClassifierService:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = None
        try:
            if config.openai_api_key:
                # **FIXED: Use async-compatible OpenAI client**
                self.openai_client = openai.AsyncOpenAI(api_key=config.openai_api_key)
                print("OpenAI Async API initialized successfully")
            else:
                raise ValueError("OpenAI API key not found in config")
        except Exception as e:
            print(f"Failed to initialize OpenAI: {e}")
            raise Exception("OpenAI API key is required for roof classification")
        
        # Initialize other services
        self.building_service = BuildingInsightsService()
        self.data_service = DataLayersService()
        self.image_processor = ImageProcessorService()
        self.gutter_calculator = GutterCalculatorService()
    
    async def classify_roof_type(self, address: str) -> Dict[str, Any]:
        """
        Complete roof classification pipeline:
        1. Geocode address
        2. Get building insights
        3. Get data layers (satellite imagery)
        4. Use OpenAI to classify roof type with visual analysis
        """
        try:
            print(f"Starting roof classification for address: {address}")
            
            # Step 1: Geocode address
            print("Step 1: Geocoding address...")
            lat, lng = geocode_address(address)
            if not lat or not lng:
                raise Exception(f"Failed to geocode address: {address}")
            print(f"Coordinates: {lat}, {lng}")
            
            # Step 2: Get building insights
            print("Step 2: Getting building insights...")
            building_data = await self.building_service.get_building_insights(address)
            print(f"Building insights retrieved")
            
            # Step 3: Get data layers
            print("Step 3: Getting data layers...")
            data_layers_result = await self.data_service.get_data_layers(address)
            print(f"Data layers retrieved")
            
            # Step 4: Process and download satellite images
            print("Step 4: Processing satellite images...")
            print(f"Data layers result keys: {list(data_layers_result.keys())}")
            print(f"Raw API response keys: {list(data_layers_result.get('raw_api_response', {}).keys())}")
            
            image_processing_result = await self.image_processor.download_and_process_images(
                data_layers_result.get("raw_api_response", {})
            )
            
            print(f"Image processing completed: {image_processing_result}")
            
            # Step 5: AI classification with visual analysis
            print("Step 5: AI roof classification with visual analysis...")
            classification = await self._ai_classify_roof_with_vision(
                building_data, 
                data_layers_result,
                image_processing_result,
                address
            )
            
            # Step 6: Calculate gutter requirements based on roof type
            print("Step 6: Calculating gutter requirements...")
            gutter_estimate = self.gutter_calculator.estimate_gutter_feet(
                building_data, 
                classification
            )
            print(f"Gutter calculation completed: {gutter_estimate.total_gutter_ft}ft")
            
            # Step 7: Return complete result with gutter estimate
            return {
                "success": True,
                "address": address,
                "geocoded_coordinates": {
                    "latitude": lat,
                    "longitude": lng
                },
                "roof_classification": classification,
                "gutter_estimate": {
                    "eave_length_ft": gutter_estimate.eave_length_ft,
                    "total_gutter_ft": gutter_estimate.total_gutter_ft,
                    "waste_factor": gutter_estimate.waste_factor,
                    "roof_type": gutter_estimate.roof_type,
                    "confidence": gutter_estimate.confidence,
                    "warnings": gutter_estimate.warnings,
                    "estimated_range": gutter_estimate.estimated_range,
                    "downspouts_estimate": gutter_estimate.downspouts_estimate,
                    "complexity_factor": gutter_estimate.complexity_factor
                },
                # **ADDED: Include image data for frontend display**
                "images": {
                    "local_image_paths": image_processing_result.get("local_image_paths", []),
                    "base64_images": image_processing_result.get("base64_images", []),
                    "image_types": image_processing_result.get("image_types", []),
                    "images_processed": image_processing_result.get("images_processed", 0)
                }
            }
            
        except Exception as e:
            print(f"Roof classification failed: {str(e)}")
            raise Exception(f"Roof classification failed: {str(e)}")
    
    async def _ai_classify_roof_with_vision(self, building_data: dict, data_layers: dict, image_processing_result: dict, address: str) -> Dict[str, Any]:
        """Use OpenAI with vision capabilities to classify the roof type based on satellite imagery and building data"""
        try:
            # Prepare the data for AI analysis
            building_raw = building_data.get("raw_api_response", {})
            data_layers_raw = data_layers.get("raw_api_response", {})
            
            # Get processed images
            print(f"Image processing result type: {type(image_processing_result)}")
            print(f"Image processing result keys: {list(image_processing_result.keys()) if isinstance(image_processing_result, dict) else 'Not a dict'}")
            
            local_image_paths = image_processing_result.get("local_image_paths", []) if isinstance(image_processing_result, dict) else []
            image_types = image_processing_result.get("image_types", []) if isinstance(image_processing_result, dict) else []
            
            print(f"Processing {len(local_image_paths)} downloaded images for AI analysis")
            
            # Create messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert roofing contractor and building inspector. Analyze the provided satellite imagery and building data to classify the roof type with high accuracy. Consider roof pitch, number of slopes, presence of dormers, and overall building geometry."
                },
                {
                    "role": "user",
                    "content": self._create_analysis_prompt(building_raw, data_layers_raw, address, image_types)
                }
            ]
            
            # Add image content if available
            if local_image_paths and len(local_image_paths) > 0:
                # **FIXED: Proper content structure for OpenAI Vision API**
                content = [
                    {
                        "type": "text",
                        "text": "Please analyze these satellite images and classify the roof type. Consider the building footprint, roof slopes, and any visible architectural features."
                    }
                ]
                
                # Add images to the content
                for image_path in local_image_paths[:3]:  # Limit to 3 images to avoid token limits
                    try:
                        with open(image_path, "rb") as image_file:
                            import base64
                            image_bytes = image_file.read()
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        })
                    except Exception as e:
                        print(f"Error reading image {image_path}: {e}")
                        continue
                
                # **FIXED: Set the entire content array, not just the first message**
                messages[1]["content"] = content
            
            # Get AI classification
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            print(f"AI Response: {ai_response}")
            
            # Extract roof type and confidence from AI response
            roof_type, confidence = self._extract_roof_classification(ai_response)
            
            # Validate roof type against building geometry
            validated_roof_type, validation_confidence = self._validate_roof_type_geometry(
                roof_type, building_data, confidence
            )
            
            # Use the validated result
            final_roof_type = validated_roof_type if validation_confidence > confidence else roof_type
            final_confidence = max(confidence, validation_confidence)
            
            print(f"Final roof classification: {final_roof_type} (confidence: {final_confidence:.2f})")
            
            return {
                "roof_type": final_roof_type,
                "confidence": final_confidence,
                "ai_response": ai_response,
                "validation_notes": f"Geometry validation: {validated_roof_type} (confidence: {validation_confidence:.2f})"
            }
            
        except Exception as e:
            print(f"AI classification failed: {str(e)}")
            # Fallback to basic classification
            return self._fallback_roof_classification(building_data)
    
    def _validate_roof_type_geometry(self, ai_roof_type: str, building_data: dict, ai_confidence: float) -> Tuple[str, float]:
        """Validate roof type classification using simple segment count logic"""
        
        try:
            building_raw = building_data.get("raw_api_response", {})
            roof_segments = building_raw.get('solarPotential', {}).get('roofSegmentStats', [])
            
            if not roof_segments:
                return ai_roof_type, ai_confidence * 0.8
            
            # **SIMPLE RULE: Segment count determines roof type**
            segment_count = len(roof_segments)
            
            # Simple geometry-based prediction
            geometry_roof_type = self._simple_segment_based_classification(segment_count)
            
            # Calculate confidence based on segment count clarity
            geometry_confidence = self._calculate_simple_confidence(segment_count, ai_roof_type, geometry_roof_type)
            
            # If geometry strongly suggests different type, use it
            if geometry_confidence > ai_confidence + 0.15:  # 15% threshold
                return geometry_roof_type, geometry_confidence
            elif geometry_confidence > ai_confidence:
                # Use geometry type but with lower confidence
                return geometry_roof_type, (ai_confidence + geometry_confidence) / 2
            else:
                # Keep AI classification but adjust confidence
                return ai_roof_type, max(ai_confidence, geometry_confidence * 0.9)
                
        except Exception as e:
            print(f"Geometry validation failed: {str(e)}")
            return ai_roof_type, ai_confidence * 0.8
    
    def _simple_segment_based_classification(self, segment_count: int) -> str:
        """Simple, reliable roof classification based on segment count"""
        
        if segment_count == 1:
            return "shed"
        elif segment_count == 2:
            return "gable"  # Most common residential roof
        elif segment_count == 3:
            return "gable"  # Gable with dormer
        elif segment_count == 4:
            # **CRITICAL FIX**: 4 segments = hip roof (not gable!)
            # This is the key insight - gable roofs have 2 main slopes
            # Hip roofs have 4 slopes (like a pyramid)
            return "hip"    
        elif segment_count == 5:
            return "hip"    # Hip with dormer
        elif segment_count >= 6:
            return "complex"  # Many segments = complex roof
        else:
            return "unknown"
    
    def _calculate_simple_confidence(self, segment_count: int, ai_type: str, geometry_type: str) -> float:
        """Calculate confidence using simple, reliable logic"""
        
        base_confidence = 0.8  # Start with high confidence for simple rules
        
        # **SEGMENT COUNT CLARITY** (the key factor)
        if segment_count == 2:
            base_confidence += 0.15  # 2 segments = very clear gable
        elif segment_count == 4:
            base_confidence += 0.1   # 4 segments = clear hip roof
        elif segment_count >= 2 and segment_count <= 5:
            base_confidence += 0.1   # Clear classification range
        elif segment_count > 5:
            base_confidence -= 0.1   # Many segments = less clear
        
        # **TYPE AGREEMENT BONUS**
        if ai_type == geometry_type:
            base_confidence += 0.1   # AI and geometry agree
        elif ai_type in ["gable", "hip"] and geometry_type in ["gable", "hip"]:
            # Both are common types, moderate confidence
            base_confidence += 0.05
        elif ai_type == "unknown" and geometry_type != "unknown":
            base_confidence += 0.1   # Geometry provides classification
        
        # **SPECIAL CASE: Gable vs Hip confusion**
        if segment_count == 2 and ai_type == "hip":
            base_confidence -= 0.2   # 2 segments unlikely to be hip
        elif segment_count == 4 and ai_type == "gable":
            base_confidence -= 0.2   # 4 segments unlikely to be simple gable
        
        # Clamp confidence between 0.4 and 0.95
        return max(0.4, min(0.95, base_confidence))
    
    def _predict_roof_type_from_geometry(self, segment_count: int, unique_azimuths: int, pitches: List[float], total_area: float) -> str:
        """Predict roof type based on geometric analysis of segments with improved gable vs hip detection"""
        
        # Analyze pitch patterns
        avg_pitch = sum(pitches) / len(pitches) if pitches else 0
        steep_segments = [p for p in pitches if p > 30]
        flat_segments = [p for p in pitches if p < 15]
        
        # **IMPROVED GABLE vs HIP DETECTION**
        # Gable roofs have exactly 2 segments with opposite azimuths (~180° difference)
        # Hip roofs have 4+ segments with more diverse azimuth patterns
        
        if segment_count == 1:
            if avg_pitch < 15:
                return "flat"
            else:
                return "shed"
                
        elif segment_count == 2:
            # **CRITICAL: Gable vs Gambrel distinction**
            if unique_azimuths == 2:
                # Check if azimuths are roughly opposite (gable) or similar (gambrel)
                # This requires azimuth data to be passed in
                return "gable"  # Most likely for 2 segments
            else:
                return "gambrel"  # Two segments with same azimuth
                
        elif segment_count == 3:
            # 3 segments usually indicate gable with dormer or hip with one side different
            if unique_azimuths >= 3:
                return "hip"  # Three different orientations
            else:
                return "gable"  # Gable with dormer
                
        elif segment_count == 4:
            # **KEY DISTINCTION: 4 segments = likely hip roof**
            if unique_azimuths >= 3:
                if any(p > 45 for p in pitches):
                    return "mansard"  # Steep slopes suggest mansard
                else:
                    return "hip"  # Four segments with different orientations = classic hip
            else:
                return "gable"  # Gable with multiple dormers
                
        elif segment_count == 5:
            # 5 segments usually indicate hip roof with dormer
            if unique_azimuths >= 4:
                return "hip"
            else:
                return "gable"  # Gable with multiple dormers
                
        elif segment_count >= 6:
            # 6+ segments = complex roof
            if unique_azimuths >= 5:
                return "complex"  # Many segments with diverse orientations
            else:
                return "hip"  # Multiple segments but fewer orientations
        
        # Fallback based on area and pitch
        if total_area > 200:  # Large roofs tend to be complex
            return "complex"
        elif avg_pitch < 20:
            return "flat"
        else:
            return "gable"  # Default to most common type
    
    def _calculate_geometry_confidence(self, ai_type: str, geometry_type: str, segment_count: int, unique_azimuths: int) -> float:
        """Calculate confidence in geometry-based classification with improved logic"""
        
        base_confidence = 0.7
        
        # **IMPROVED TYPE AGREEMENT LOGIC**
        # Gable and hip are often confused, so give bonus for agreement
        if ai_type == geometry_type:
            base_confidence += 0.2
        elif (ai_type == "gable" and geometry_type == "gable") or (ai_type == "hip" and geometry_type == "hip"):
            base_confidence += 0.15  # High confidence for these common types
        elif ai_type in ["complex", "unknown"] and geometry_type != "unknown":
            base_confidence += 0.1  # Geometry provides more specific classification
        
        # **SEGMENT COUNT CONFIDENCE** (more precise)
        if segment_count == 2:
            base_confidence += 0.15  # 2 segments = very clear gable/gambrel
        elif segment_count == 4:
            base_confidence += 0.1   # 4 segments = clear hip roof
        elif segment_count >= 2 and segment_count <= 6:
            base_confidence += 0.1   # Optimal segment count for analysis
        elif segment_count > 6:
            base_confidence -= 0.1   # Too many segments can be confusing
        
        # **AZIMUTH DIVERSITY CONFIDENCE** (key for gable vs hip)
        if unique_azimuths == 2:
            base_confidence += 0.1   # 2 azimuths = likely gable
        elif unique_azimuths >= 3 and unique_azimuths <= 4:
            base_confidence += 0.1   # 3-4 azimuths = likely hip
        elif unique_azimuths >= 5:
            base_confidence += 0.05  # 5+ azimuths = complex
        elif unique_azimuths == 1:
            base_confidence -= 0.1   # Single azimuth makes classification harder
        
        # **SPECIAL CASE: Gable vs Hip confusion**
        if segment_count == 4 and unique_azimuths >= 3:
            if geometry_type == "hip":
                base_confidence += 0.1  # 4 segments with 3+ azimuths strongly suggests hip
            elif geometry_type == "gable":
                base_confidence -= 0.1  # 4 segments unlikely to be simple gable
        
        # Clamp confidence between 0.3 and 0.95
        return max(0.3, min(0.95, base_confidence))
    
    def _fallback_roof_classification(self, building_data: dict) -> Dict[str, Any]:
        """Fallback classification when AI analysis fails"""
        
        try:
            building_raw = building_data.get("raw_api_response", {})
            roof_segments = building_raw.get('solarPotential', {}).get('roofSegmentStats', [])
            
            if roof_segments:
                # Use simple segment-count-based classification as fallback
                segment_count = len(roof_segments)
                fallback_type = self._simple_segment_based_classification(segment_count)
                
                return {
                    "roof_type": fallback_type,
                    "confidence": 0.7,  # Good confidence for simple rules
                    "ai_response": "AI analysis failed, using segment-count-based classification",
                    "validation_notes": f"Fallback: {segment_count} segments = {fallback_type}"
                }
            else:
                return {
                    "roof_type": "unknown",
                    "confidence": 0.3,
                    "ai_response": "No roof segments available for analysis",
                    "validation_notes": "Insufficient data for classification"
                }
                
        except Exception as e:
            print(f"Fallback classification failed: {str(e)}")
            return {
                "roof_type": "unknown",
                "confidence": 0.2,
                "ai_response": "Classification system error",
                "validation_notes": f"System error: {str(e)}"
            }
    
    def _extract_roof_classification(self, ai_response: str) -> Tuple[str, float]:
        """Extract roof type and confidence from AI response"""
        
        try:
            # Try to parse JSON response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    roof_type = result.get('roof_type', 'unknown')
                    confidence = result.get('confidence', 0.8)
                    return roof_type, confidence
                except json.JSONDecodeError:
                    pass
            
            # Fallback: look for roof type in text
            roof_types = ['flat', 'shed', 'gable', 'gambrel', 'hip', 'mansard', 'complex']
            found_type = 'unknown'
            
            for roof_type in roof_types:
                if roof_type.lower() in ai_response.lower():
                    found_type = roof_type
                    break
            
            # Estimate confidence based on response quality
            if 'confident' in ai_response.lower() or 'clear' in ai_response.lower():
                confidence = 0.9
            elif 'appears' in ai_response.lower() or 'seems' in ai_response.lower():
                confidence = 0.7
            elif 'unclear' in ai_response.lower() or 'difficult' in ai_response.lower():
                confidence = 0.5
            else:
                confidence = 0.7
            
            return found_type, confidence
            
        except Exception as e:
            print(f"Error extracting roof classification: {str(e)}")
            return 'unknown', 0.5
    

    
    def _create_analysis_prompt(self, building_raw: dict, data_layers_raw: dict, address: str, image_types: List[str]) -> str:
        """Create a SIMPLE, focused prompt for roof classification with 80% data focus and 20% visual focus"""
        
        # Extract only essential data - segment count is the key
        roof_segments = building_raw.get('solarPotential', {}).get('roofSegmentStats', [])
        whole_roof_stats = building_raw.get('solarPotential', {}).get('wholeRoofStats', {})
        
        # **SIMPLE RULE: Segment count determines roof type**
        segment_count = len(roof_segments)
        
        # Create ultra-simple prompt
        prompt = f"""
You are a roofing expert. Classify this roof using 80% data analysis and 20% visual inspection.

**CRITICAL RULE: Count the roof segments first, then classify:**

**SEGMENT COUNT = ROOF TYPE:**
- 1 segment = SHED or FLAT
- 2 segments = GABLE (most common residential roof)
- 3 segments = GABLE with dormer
- 4+ segments = HIP roof
- 6+ segments = COMPLEX roof

**BUILDING DATA (80% of decision):**
- Total roof segments: {segment_count}
- Total roof area: {whole_roof_stats.get('groundAreaMeters2', 0):.1f} m²

**SEGMENT DETAILS:**
"""
        
        # Add only essential segment info
        for i, segment in enumerate(roof_segments):
            prompt += f"""
        Segment {i+1}:
- Pitch: {segment.get('pitchDegrees', 0):.1f}°
- Azimuth: {segment.get('azimuthDegrees', 0):.1f}°
- Area: {segment.get('stats', {}).get('groundAreaMeters2', 0):.1f} m²
        """
        
        prompt += f"""

**VISUAL CHECK (20% of decision):**
Look at the satellite image and verify:
- Does the roof have 2 main slopes (gable) or 4+ slopes (hip)?
- Is it a simple triangular shape (gable) or pyramid-like (hip)?

**FINAL CLASSIFICATION:**
Based on {segment_count} segments, this is most likely a **{'GABLE' if segment_count <= 3 else 'HIP' if segment_count <= 5 else 'COMPLEX'}** roof.

**RESPONSE FORMAT:**
Return ONLY this JSON:
{{
    "roof_type": "gable|hip|shed|gambrel|mansard|flat|complex",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}}

**REMEMBER: 2 segments = GABLE, 4+ segments = HIP**
        """
        
        return prompt
