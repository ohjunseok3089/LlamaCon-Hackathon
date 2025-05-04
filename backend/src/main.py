import os
import shutil
import traceback
import json
import base64
import uuid
from pathlib import Path
import cv2
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Path as FastApiPath, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
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

UPLOAD_DIR = "uploaded_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True) # Create the directory if it doesn't exist

def process_video_file(video_path: Path, frame_interval: int = 10) -> List[str]:
    base64_frames: List[str] = []
    if not video_path.is_file():
        print(f"!!! Error: Video file not found at {video_path}")
        return base64_frames

    print(f"--- Processing video file: {video_path} ---")
    # TODO: Add audio extraction and processing logic here (Placeholder)
    # Example: extract_audio(video_path) -> audio_data
    #          transcribe_audio(audio_data) -> transcript

    cap = cv2.VideoCapture(str(video_path)) # Use string representation of Path
    if not cap.isOpened():
        print(f"!!! Error: Could not open video file: {video_path}")
        return base64_frames

    frame_count = 0
    extracted_count = 0
    try:
        while True:
            ret, frame = cap.read() # ret is True if frame read successfully

            if not ret:
                print("--- End of video or error reading frame ---")
                break # Exit loop if no frame is returned

            # Check if the current frame is one we want to extract
            if frame_count % frame_interval == 0:
                print(f"--- Extracting frame {frame_count} ---")
                # Encode the frame as JPEG in memory
                is_success, buffer = cv2.imencode(".jpg", frame)
                if is_success:
                    # Convert the buffer (bytes) to a base64 string
                    jpg_as_text = base64.b64encode(buffer).decode("utf-8")
                    base64_frames.append(jpg_as_text)
                    extracted_count += 1
                else:
                    print(f"!!! Warning: Failed to encode frame {frame_count} to JPEG")

            frame_count += 1

    except Exception as e:
         print(f"!!! Error during video processing loop: {e}")
         traceback.print_exc()
    finally:
        cap.release() # Release the video capture object
        print(f"--- Finished processing video. Extracted {extracted_count} frames. ---")

    return base64_frames

@app.get("/")
async def root():
    return {"message": "Llama API is running. Send POST requests to /ask_llama"}

class UploadResponse(BaseModel):
    stream_url: str
    filename: str

@app.post("/ask_llama", response_model=UploadResponse)
async def ask_llama_upload(video: UploadFile = File(...)):
    """
    Receives a video file, saves it with a unique ID,
    and returns a unique URL for streaming the results.
    """
    original_filename = video.filename
    file_id = str(uuid.uuid4())
    file_ext = Path(original_filename).suffix or '.webm'
    save_filename = f"{file_id}{file_ext}"
    file_location = f"{UPLOAD_DIR}/{save_filename}"

    try:
        print(f"Receiving file: {original_filename}, Content-Type: {video.content_type}")
        print(f"Generating ID: {file_id}")
        print(f"Attempting to save to: {file_location}")

        # Save the file
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        print(f"Successfully saved file to: {file_location}")

        # Construct the stream URL path (relative)
        stream_url_path = f"/stream/{file_id}" # URL includes the unique ID

        # Return the unique URL for the frontend to connect to
        return UploadResponse(
            stream_url=stream_url_path,
            filename=original_filename
        )

    except Exception as e:
        print(f"!!! Error saving file {original_filename}: {e}")
        traceback.print_exc()
        # Clean up partially saved file if error occurred during save
        if file_location.exists():
             try: file_location.unlink()
             except OSError: pass
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")
    finally:
        await video.close()

@app.get("/stream/{file_id}")
async def stream_results(
    file_id: str = FastApiPath(..., title="Unique ID of the uploaded file", regex="^[a-fA-F0-9-]{36}$"),
    prompt: Optional[str] = Query(None, title="Optional user prompt for Llama")
):
    video_path: Optional[Path] = None
    for item in UPLOAD_DIR.iterdir():
        if item.is_file() and item.stem == file_id:
             video_path = item
             break

    if not video_path or not video_path.exists():
        print(f"!!! Error: Could not find video file for ID {file_id} in {UPLOAD_DIR}")
        async def error_stream_gen():
            error_payload = json.dumps({"error": "File not found", "detail": f"Video for ID {file_id} not found or expired."})
            yield f"event: error\ndata: {error_payload}\n\n" # Custom event type 'error'
        return StreamingResponse(error_stream_gen(), media_type="text/event-stream", status_code=404)

    print(f"--- Found video file: {video_path} ---")

    try:
        image_frames_base64 = process_video_file(video_path)
        final_prompt = prompt
        if not final_prompt:
             final_prompt = "Describe the key events shown in these video frames."

        if not image_frames_base64:
             print("--- stream: No frames extracted from video, cannot call Llama ---")
             async def error_stream_gen():
                  error_payload = json.dumps({"error": "Video processing failed", "detail": "No frames extracted."})
                  yield f"event: error\ndata: {error_payload}\n\n"
             return StreamingResponse(error_stream_gen(), media_type="text/event-stream", status_code=400)

        # --- Call LlamaProcessor and return the stream ---
        return llama_processor.process_images_stream(
            images=image_frames_base64,
            user_prompt=final_prompt
        )

    except Exception as e:
        print(f"!!! Error during streaming for {file_id}: {e}")
        traceback.print_exc()
        async def error_stream_gen():
             error_payload = json.dumps({"error": "Processing Error", "detail": str(e)})
             yield f"event: error\ndata: {error_payload}\n\n"
        return StreamingResponse(error_stream_gen(), media_type="text/event-stream", status_code=500)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=1234, reload=True)
