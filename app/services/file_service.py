import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Tuple

UPLOAD_DIR = Path("input")
OUTPUT_DIR = Path("separated")
MODEL_NAME = "htdemucs_6s"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Allowed audio formats for processing
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}

def validate_and_save_upload(file: UploadFile) -> Tuple[str, str]:
    """
    Validates uploaded audio and saves it dynamically to disk.
    Returns: (file_id, absolute_file_path)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    try:
        # Standard block-based saving for larger files without exhausting RAM
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save uploaded file locally")
        
    return file_id, str(file_path)

def get_output_folder(file_id: str) -> Path:
    return OUTPUT_DIR / MODEL_NAME / file_id

def cleanup_upload(file_path: str):
    """
    Removes temporary upload artifact if needed, avoiding leaked disk space.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # In a robust scenario, maybe trace log, but don't crash
        pass
