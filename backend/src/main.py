import base64
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from llama import LlamaProcessor
import traceback
import json

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
    images: List[str]  # Base64 encoded image strings
    user_prompt: Optional[str] = None # Include prompt in the body

def video_extract(video_file):
    """Extract video file into frames and audio"""
    # TODO: Implement video extraction; Video -> image frames and audio
    # TODO: Audio -> Speech to Text


    pass

@app.get("/")
async def root():
    return {"message": "Llama API is running. Send POST requests to /ask_llama"}

# Updated endpoint to accept prompt in body and return stream
@app.post("/ask_llama")
async def ask_llama(image_data: ImageData): # Get images and prompt from body
    try:
        # Return type: StreamingResponse
        return llama_processor.process_images_stream(
            image_data.images,
            image_data.user_prompt
        )
    except Exception as e:
        print(f"!!! Error in /ask_llama endpoint: {e}")
        traceback.print_exc()
        async def error_stream_gen():
             error_payload = json.dumps({"error": "Failed to start stream", "detail": str(e)})
             yield f"data: {error_payload}\n\n"
        return StreamingResponse(error_stream_gen(), media_type="text/event-stream", status_code=500)

# For handling raw JSON if needed
@app.post("/upload_raw")
async def upload_raw(request: Request):
    # Under Construction
    
    # try:
    #     data = await request.json()
    #     images = data.get("images", [])
    #     num_images = len(images)
        
    #     return JSONResponse(
    #         content={
    #             "success": True,
    #             "message": f"Successfully received {num_images} images via raw JSON",
    #             "count": num_images
    #         },
    #         status_code=200
    #     )
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))

# Run the server if this script is executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
