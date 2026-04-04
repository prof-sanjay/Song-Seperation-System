import librosa
import numpy as np

def detect_pitch(file_path: str):
    """
    Detects pitch from an audio file using YIN.
    """
    y, sr = librosa.load(file_path)
    f0 = librosa.yin(y, fmin=50, fmax=2000)
    
    # Remove unvoiced (nan) values
    f0_clean = [freq for freq in f0 if not np.isnan(freq)]
    
    # Convert to notes
    notes = librosa.hz_to_note(f0_clean)
    
    return notes[:50]  # Example sample output
