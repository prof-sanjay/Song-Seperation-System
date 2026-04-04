from separate import separate_audio
import sys
import os

# Adjust path to load from our new utils folder if needed, 
# or just import relative since it's modular
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.utils.scale import detect_key

INPUT_FILE = "input/Perfect.mp3"  # Updated to the existing input file

# Step 1: Separate
OUT_DIR = "separated"
MODEL = "htdemucs_6s"
separate_audio(INPUT_FILE, output_dir=OUT_DIR, model=MODEL)

# Step 2: Locate output
song_name = os.path.splitext(os.path.basename(INPUT_FILE))[0]
# Demucs 6s saves to: <output_dir>/<model_name>/<song_name>
song_folder = f"{OUT_DIR}/{MODEL}/{song_name}"

# Step 3: Karaoke
from shutil import copyfile
copyfile(f"{song_folder}/other.wav", f"{song_folder}/karaoke.wav")

# Step 4: Key & Scale Detection
key_info = detect_key(f"{song_folder}/other.wav")

print("Detected Key Info:", key_info)