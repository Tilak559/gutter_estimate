from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os

from routers.geocode import solar as geocode_router
from routers.building_insights import building_insights as building_insights_router
from routers.data_layers import data_layers as data_layers_router
from routers.roof_classification import roof_classification as roof_classification_router

app = FastAPI(title="Gutter Estimation API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(geocode_router)
app.include_router(building_insights_router)
app.include_router(data_layers_router)
app.include_router(roof_classification_router)

@app.get("/")
async def root():
    return {"message": "Gutter Estimation API"}

@app.get("/api/debug/images")
async def debug_images():
    """Debug endpoint to list available images"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(current_dir, "images")
    
    try:
        if os.path.exists(images_dir):
            images = os.listdir(images_dir)
            image_info = []
            
            for img in images:
                img_path = os.path.join(images_dir, img)
                if os.path.isfile(img_path):
                    stat = os.stat(img_path)
                    image_info.append({
                        "filename": img,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created": stat.st_ctime,
                        "modified": stat.st_mtime
                    })
            
            return {
                "images_directory": images_dir,
                "total_images": len(image_info),
                "images": image_info
            }
        else:
            return {"error": f"Images directory does not exist: {images_dir}"}
    except Exception as e:
        return {"error": f"Error listing images: {str(e)}"}

@app.get("/api/images/{filename}")
async def get_image(filename: str):
    """Serve satellite images from the backend/images directory"""
    # Get the absolute path to the images directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(current_dir, "images")
    image_path = os.path.join(images_dir, filename)
    
    print(f"Requested image: {filename}")
    print(f"Images directory: {images_dir}")
    print(f"Full image path: {image_path}")
    print(f"Path exists: {os.path.exists(image_path)}")
    
    if os.path.exists(image_path):
        # Determine media type based on file extension
        if filename.endswith('.png'):
            media_type = "image/png"
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            media_type = "image/jpeg"
        else:
            media_type = "image/png"  # Default
        
        return FileResponse(image_path, media_type=media_type)
    else:
        # List available images for debugging
        try:
            available_images = os.listdir(images_dir) if os.path.exists(images_dir) else []
            print(f"Available images: {available_images}")
        except Exception as e:
            print(f"Error listing images: {e}")
            available_images = []
        
        return {"error": f"Image not found: {filename}", "available_images": available_images}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
