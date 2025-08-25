#!/usr/bin/env python3
"""
Test script to validate improved roof classification logic
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.roof_classifier import RoofClassifierService

def test_roof_classification_logic():
    """Test the improved roof classification logic"""
    
    print("🧪 Testing Improved Roof Classification Logic")
    print("=" * 60)
    
    # Create classifier instance
    classifier = RoofClassifierService()
    
    # Test cases for different roof types
    test_cases = [
        {
            'name': 'Simple Gable (2 segments, opposite azimuths)',
            'segments': [
                {'pitchDegrees': 30, 'azimuthDegrees': 0, 'stats': {'groundAreaMeters2': 50}},
                {'pitchDegrees': 30, 'azimuthDegrees': 180, 'stats': {'groundAreaMeters2': 50}}
            ],
            'expected': 'gable'
        },
        {
            'name': 'Hip Roof (4 segments, diverse azimuths)',
            'segments': [
                {'pitchDegrees': 25, 'azimuthDegrees': 0, 'stats': {'groundAreaMeters2': 40}},
                {'pitchDegrees': 25, 'azimuthDegrees': 90, 'stats': {'groundAreaMeters2': 40}},
                {'pitchDegrees': 25, 'azimuthDegrees': 180, 'stats': {'groundAreaMeters2': 40}},
                {'pitchDegrees': 25, 'azimuthDegrees': 270, 'stats': {'groundAreaMeters2': 40}}
            ],
            'expected': 'hip'
        },
        {
            'name': 'Gable with Dormer (3 segments)',
            'segments': [
                {'pitchDegrees': 30, 'azimuthDegrees': 0, 'stats': {'groundAreaMeters2': 60}},
                {'pitchDegrees': 30, 'azimuthDegrees': 180, 'stats': {'groundAreaMeters2': 60}},
                {'pitchDegrees': 25, 'azimuthDegrees': 90, 'stats': {'groundAreaMeters2': 20}}
            ],
            'expected': 'gable'
        },
        {
            'name': 'Complex Roof (6+ segments)',
            'segments': [
                {'pitchDegrees': 25, 'azimuthDegrees': 0, 'stats': {'groundAreaMeters2': 30}},
                {'pitchDegrees': 25, 'azimuthDegrees': 45, 'stats': {'groundAreaMeters2': 30}},
                {'pitchDegrees': 25, 'azimuthDegrees': 90, 'stats': {'groundAreaMeters2': 30}},
                {'pitchDegrees': 25, 'azimuthDegrees': 135, 'stats': {'groundAreaMeters2': 30}},
                {'pitchDegrees': 25, 'azimuthDegrees': 180, 'stats': {'groundAreaMeters2': 30}},
                {'pitchDegrees': 25, 'azimuthDegrees': 225, 'stats': {'groundAreaMeters2': 30}}
            ],
            'expected': 'complex'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        # Create mock building data
        mock_building_data = {
            'raw_api_response': {
                'solarPotential': {
                    'roofSegmentStats': test_case['segments'],
                    'wholeRoofStats': {'groundAreaMeters2': 200}
                },
                'center': {'latitude': 40.0, 'longitude': -74.0}
            }
        }
        
        # Test azimuth pattern analysis
        azimuths = [seg['azimuthDegrees'] for seg in test_case['segments']]
        azimuth_pattern = classifier._analyze_azimuth_patterns(azimuths)
        
        print(f"   Segments: {len(test_case['segments'])}")
        print(f"   Azimuths: {azimuths}")
        print(f"   Pattern: {azimuth_pattern['pattern']} (confidence: {azimuth_pattern['confidence']:.2f})")
        
        # Test geometry prediction
        segment_count = len(test_case['segments'])
        unique_azimuths = len(set(round(az, 5) for az in azimuths))
        pitches = [seg['pitchDegrees'] for seg in test_case['segments']]
        total_area = sum(seg['stats']['groundAreaMeters2'] for seg in test_case['segments'])
        
        geometry_type = classifier._predict_roof_type_from_geometry_with_azimuth(
            segment_count, unique_azimuths, pitches, total_area, azimuth_pattern
        )
        
        print(f"   Predicted: {geometry_type}")
        print(f"   Expected: {test_case['expected']}")
        print(f"   ✅ {'CORRECT' if geometry_type == test_case['expected'] else '❌ INCORRECT'}")
        
        # Test confidence calculation
        confidence = classifier._calculate_geometry_confidence_with_azimuth(
            geometry_type, geometry_type, segment_count, unique_azimuths, azimuth_pattern
        )
        print(f"   Confidence: {confidence:.2f}")

if __name__ == "__main__":
    test_roof_classification_logic()
