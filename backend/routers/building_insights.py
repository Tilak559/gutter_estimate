from fastapi import APIRouter, HTTPException
from services.building_insights import BuildingInsightsService

building_insights = APIRouter(prefix="/api/v1", tags=["building-insights"])

# Initialize service
building_service = BuildingInsightsService()

@building_insights.get("/building-insights")
async def get_building_insights(address: str):
    """
    Get building insights for a given address
    """
    try:
        print(f"Getting building insights for address: {address}")
        
        building_data = await building_service.get_building_insights(address)
        
        return {
            "success": True,
            "address": address,
            "building_insights": building_data
        }
        
    except Exception as e:
        print(f"Error getting building insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@building_insights.get("/building-insights/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Building Insights API is running"}
