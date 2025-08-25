from fastapi import APIRouter, HTTPException
from services.data_layers import DataLayersService

data_layers = APIRouter(prefix="/api/v1", tags=["data-layers"])

# Initialize service
data_service = DataLayersService()

@data_layers.get("/data-layers")
async def get_data_layers(address: str):
    """
    Get data layers for a given address
    """
    try:
        print(f"Getting data layers for address: {address}")
        
        data_layers_result = await data_service.get_data_layers(address)
        
        return {
            "success": True,
            "address": address,
            "data_layers": data_layers_result
        }
        
    except Exception as e:
        print(f"Error getting data layers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@data_layers.get("/data-layers/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Data Layers API is running"}
