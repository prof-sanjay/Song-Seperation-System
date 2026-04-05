import shutil
import json
import logging
from utils.demucs import run_demucs
from utils.scale import detect_key
from services.file_service import get_output_folder, OUTPUT_DIR, MODEL_NAME, cleanup_upload

logger = logging.getLogger(__name__)

def process_audio_pipeline(file_path: str, file_id: str):
    """
    Heavy orchestration step (separated to stay off the async event loop).
    Executes Demucs, copies karaoke stems, and runs Pitch detection sequentially.
    """
    try:
        logger.info(f"Starting Demucs separation for {file_id}")
        run_demucs(file_path, output_dir=str(OUTPUT_DIR), model=MODEL_NAME)
        
        song_folder = get_output_folder(file_id)
        if not song_folder.exists():
            logger.error(f"Demucs output logic failure. Missing dir: {file_id}")
            return
            
        karaoke_path = song_folder / "karaoke.wav"
        other_path = song_folder / "other.wav"
        key_path = song_folder / "key.json"
        
        if other_path.exists():
            logger.info(f"Generating karaoke track for {file_id}")
            shutil.copyfile(other_path, karaoke_path)
            
            logger.info(f"Starting Scale/Key detection for {file_id}")
            key_info = detect_key(str(other_path))
            
            with open(key_path, "w") as f:
                json.dump(key_info, f)
                
        logger.info(f"Pipeline processing finished completely for {file_id}")
        
    except Exception as e:
        logger.error(f"Processing failed for {file_id} - Error: {str(e)}")
        # Extension: Consider writing a 'failure.json' in chunk folder for API to read.
        
    finally:
        # Prevent input/ folder from blowing up servers after large inputs
        logger.info(f"Self-cleaning uploaded artifact: {file_path}")
        cleanup_upload(file_path)
