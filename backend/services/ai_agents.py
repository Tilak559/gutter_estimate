import openai
import asyncio
from typing import Dict, Any
import os
from config import config

class AIAgentService:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = None
        try:
            if config.openai_api_key:
                self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
                print("OpenAI API initialized successfully")
            else:
                raise ValueError("OpenAI API key not found in config")
        except Exception as e:
            print(f"Failed to initialize OpenAI: {e}")
            raise Exception("OpenAI API key is required for roof classification")
    
    async def classify_roof_type(self, image_url: str, stats: dict) -> Dict[str, Any]:
        """
        Multi-agent system for roof classification:
        1. Vision Agent: Analyzes satellite image
        2. Stats Agent: Analyzes segment statistics
        3. Final Agent: Combines both for final decision
        """
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        try:
            # Vision Agent
            vision_analysis = await self._vision_agent(image_url)
            
            # Stats Agent
            stats_analysis = await self._stats_agent(stats)
            
            # Final Agent
            final_classification = await self._final_agent(vision_analysis, stats_analysis)
            
            return final_classification
            
        except Exception as e:
            print(f"AI classification failed: {e}")
            raise Exception(f"Roof classification failed: {str(e)}")
    
    async def _vision_agent(self, image_url: str) -> str:
        """Vision agent analyzes the satellite image"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a roof classification expert. Analyze this image and describe what you see. If it's a placeholder image, acknowledge that and provide general roof classification guidance based on typical residential patterns."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and describe what you see. If it's a satellite image, identify the roof structure, shape, and type (gable, hip, flat, mansard, gambrel, shed, or complex). If it's a placeholder image, acknowledge that and provide general guidance for typical residential roof patterns in the area."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Vision analysis failed: {str(e)}")
    
    async def _stats_agent(self, stats: dict) -> str:
        """Stats agent analyzes the segment statistics"""
        try:
            segments = stats.get("segments", [])
            total_area = stats.get("totalGroundAreaMeters2", 0)
            
            # Analyze pitch distribution
            pitches = [seg.get("pitchDegrees", 0) for seg in segments]
            avg_pitch = sum(pitches) / len(pitches) if pitches else 0
            
            # Analyze azimuth distribution
            azimuths = [seg.get("azimuthDegrees", 0) for seg in segments]
            
            analysis = f"""
            Roof Analysis:
            - Number of segments: {len(segments)}
            - Total ground area: {total_area:.1f} m²
            - Average pitch: {avg_pitch:.1f}°
            - Pitch range: {min(pitches):.1f}° to {max(pitches):.1f}°
            - Azimuth spread: {max(azimuths) - min(azimuths):.1f}°
            """
            
            return analysis
        except Exception as e:
            raise Exception(f"Stats analysis failed: {str(e)}")
    
    async def _final_agent(self, vision_analysis: str, stats_analysis: str) -> Dict[str, Any]:
        """Final agent combines vision and stats for classification"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a roof classification expert. Based on the vision analysis and statistical data, classify the roof type and provide confidence level."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Vision Analysis: {vision_analysis}
                        
                        Statistical Analysis: {stats_analysis}
                        
                        Based on both analyses, classify this roof as one of: gable, hip, flat, mansard, gambrel, shed, or complex.
                        
                        Return your response in this exact JSON format:
                        {{
                            "roof_type": "gable",
                            "confidence": 0.85,
                            "reasoning": "Brief explanation of classification"
                        }}
                        """
                    }
                ],
                max_tokens=200
            )
            
            # Parse the response
            content = response.choices[0].message.content
            # Extract JSON from response (handle markdown formatting)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            import json
            result = json.loads(content)
            return result
            
        except Exception as e:
            raise Exception(f"Final classification failed: {str(e)}")
