from fastapi import APIRouter, HTTPException
from services.roof_classifier import RoofClassifierService

roof_classification = APIRouter(prefix="/api/v1", tags=["roof-classification"])

# Initialize service
roof_service = RoofClassifierService()

@roof_classification.post("/classify-roof")
async def classify_roof(address: str):
    """
    Complete roof classification endpoint that:
    1. Calls geocode API
    2. Calls building insights API
    3. Calls data layers API
    4. Uses OpenAI to classify roof type
    
    Accepts address as query parameter
    """
    try:
        print(f"Starting complete roof classification for address: {address}")
        
        # Call the roof classification service
        result = await roof_service.classify_roof_type(address)
        
        return {
            "success": True,
            "message": "Roof classification completed successfully",
            "data": result
        }
        
    except Exception as e:
        print(f"Error in roof classification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@roof_classification.get("/classify-roof")
async def classify_roof_get(address: str):
    """
    GET endpoint for roof classification (same functionality as POST)
    """
    try:
        print(f"Starting complete roof classification for address: {address}")
        
        # Call the roof classification service
        result = await roof_service.classify_roof_type(address)
        
        return {
            "success": True,
            "message": "Roof classification completed successfully",
            "data": result
        }
        
    except Exception as e:
        print(f"Error in roof classification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@roof_classification.get("/classify-roof/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Roof Classification API is running"}
