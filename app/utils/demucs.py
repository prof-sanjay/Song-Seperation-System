import subprocess
import os

def run_demucs(input_path: str, output_dir: str, model: str = "htdemucs_6s"):
    """
    Separates the audio file into multiple stems using Demucs.
    """
    os.makedirs(output_dir, exist_ok=True)
    command = [
        "python", "-m", "demucs.separate",
        "-n", model,
        "-o", output_dir,
        input_path
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Demucs processing failed: {e}")
