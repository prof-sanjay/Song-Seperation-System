import os
import uuid
import shutil
import json
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from scripts.separate import separate_audio
from scripts.pitch import detect_pitch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Separation API", 
    description="API to separate audio into stems and detect pitch using Demucs & YIN"
)

UPLOAD_DIR = "input"
OUTPUT_DIR = "separated"
MODEL_NAME = "htdemucs_6s"

# Ensure directories exist upon startup
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def process_audio(file_path: str, file_id: str):
    """
    Background task to process audio: separation and pitch detection.
    """
    try:
        logger.info(f"Starting background processing for {file_id}")
        
        # Run Demucs separation
        # Demucs will save outputs to: {OUTPUT_DIR}/{MODEL_NAME}/{file_id}/
        separate_audio(file_path, output_dir=OUTPUT_DIR, model=MODEL_NAME)
        
        song_folder = Path(OUTPUT_DIR) / MODEL_NAME / file_id
        
        if not song_folder.exists():
            logger.error(f"Output folder not found for {file_id}")
            return
            
        karaoke_path = song_folder / "karaoke.wav"
        other_path = song_folder / "other.wav"
        notes_path = song_folder / "notes.json"
        
        if other_path.exists():
            # Generate karaoke track by copying the 'other' stem
            shutil.copyfile(other_path, karaoke_path)
            logger.info(f"Karaoke track generated for {file_id}")
            
            # Run pitch detection
            logger.info(f"Starting pitch detection for {file_id}")
            notes = detect_pitch(str(other_path))
            
            # Save notes to JSON
            with open(notes_path, "w") as f:
                json.dump(notes, f)
            logger.info(f"Pitch detection complete for {file_id}")
            
        logger.info(f"Processing complete for {file_id}")
    except Exception as e:
        logger.error(f"Error processing {file_id}: {str(e)}")


@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload an audio file for processing.
    The file will be saved locally and processing will start in the background.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
        
    # Generate unique filename via UUID
    file_id = str(uuid.uuid4())
    # Preserving the original file extension ensures ffmpeg processes correctly
    file_extension = os.path.splitext(file.filename)[1] or ".mp3"
    filename = f"{file_id}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # chunk-based file write to optimize for large files
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file locally")
        
    # Start background processing
    background_tasks.add_task(process_audio, file_path, file_id)
    
    return {
        "message": "File uploaded successfully. Processing started.",
        "file_id": file_id,
        "original_filename": file.filename,
        "status_url": f"/status/{file_id}"
    }


@app.get("/status/{file_id}")
def get_status(file_id: str):
    """
    Check the processing status of an uploaded track.
    """
    song_folder = Path(OUTPUT_DIR) / MODEL_NAME / file_id
    
    # We define completion by the presence of our final metadata file (notes.json)
    if song_folder.exists():
        notes_path = song_folder / "notes.json"
        
        status = "completed" if notes_path.exists() else "processing"
        
        files_available = []
        if status == "completed":
            files_available = [f.name for f in song_folder.glob("*.wav")]
            files_available.append("notes.json")
            
        return {
            "status": status,
            "file_id": file_id,
            "files_available": files_available
        }
    else:
        # Either processing hasn't yielded files yet, or the ID is invalid
        return {"status": "processing_or_not_found", "file_id": file_id}


@app.get("/download/{file_id}/{track_name}")
def download_file(file_id: str, track_name: str):
    """
    Download a specific track (e.g., 'vocals.wav', 'karaoke.wav', 'notes.json')
    """
    # Sanitize track_name to prevent path traversal
    safe_track_name = os.path.basename(track_name)
    
    file_path = Path(OUTPUT_DIR) / MODEL_NAME / file_id / safe_track_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    media_type = "application/json" if safe_track_name.endswith(".json") else "audio/wav"
    
    return FileResponse(
        path=file_path,
        filename=f"{file_id}_{safe_track_name}",
        media_type=media_type
    )