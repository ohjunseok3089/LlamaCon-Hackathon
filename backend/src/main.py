import base64
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from llama import LlamaProcessor

# Create FastAPI app
app = FastAPI(title="Image Receiver API")

# Add CORS middleware to allow cross-origin requests from JavaScript
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

llama_processor = LlamaProcessor()

# Define models for request validation
class ImageData(BaseModel):
    images: List[str]  # Base64 encoded images
    metadata: Optional[dict] = None

@app.get("/")
async def root():
    return {"message": "Image Receiver API is running. Send POST requests to /ask_llama"}

@app.post("/ask_llama")
async def ask_llama(image_data: ImageData, user_prompt: str):
    try:
        # Process received images
        num_images = len(image_data.images)

        # Llama Processing
        response_message = llama_processing(image_data.images, user_prompt)
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Successfully received {num_images} images",
                "count": num_images,
                "metadata": image_data.metadata,
                "response": response_message
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# For handling raw JSON if needed
@app.post("/upload_raw")
async def upload_raw(request: Request):
    try:
        data = await request.json()
        images = data.get("images", [])
        num_images = len(images)
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Successfully received {num_images} images via raw JSON",
                "count": num_images
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def llama_processing(images, user_prompt):
    is_success = False
    response_message = "Failed to process images"
    system_prompt = ""

    response_message = llama_processor.process_images(images, user_prompt)

    response_json = {
        "success": is_success,
        "message": response_message,
        "count": 0
    }
    return response_message

# Run the server if this script is executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
