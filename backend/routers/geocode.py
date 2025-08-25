from fastapi import APIRouter, HTTPException
from services.geocode import geocode_address

solar = APIRouter(prefix="/api/v1", tags=["geocode"])

@solar.get("/coordinates")
async def get_coordinates(address: str):
    lat, lng = geocode_address(address)
    if lat and lng:
        return {"latitude": lat, "longitude": lng}
    else:
        raise HTTPException(status_code=400, detail="Failed to geocode address")