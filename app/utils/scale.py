import librosa
import numpy as np

# Krumhansl-Schmuckler key profiles
# Values for major keys
MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
# Values for minor keys
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def detect_key(file_path: str):
    """
    Detects the musical key and scale using the Krumhansl-Schmuckler algorithm 
    by extracting Chroma features, and correlating them against known profiles.
    """
    try:
        # 1. Load audio and perform harmonic-percussive separation.
        # This vastly improves accuracy because noise/drums distort chroma vectors.
        y, sr = librosa.load(file_path, sr=22050)
        
        # Edge case: Pure silence or flat audio
        if len(y) == 0 or np.max(np.abs(y)) < 1e-4:
            return {"key": "Silent", "confidence": 0.0}
            
        y_harmonic, _ = librosa.effects.hpss(y)
        
        # 2. Extract Chroma Features
        # Using chroma_cqt (Constant-Q Transform) is superior to chroma_stft 
        # because the frequency bins in CQT align exactly with the logarithmically 
        # spaced notes of the Western musical scale, avoiding STFT's linear leakage.
        # Alternatively, chroma_cens can be used for deep structural analysis invariant to dynamics.
        chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
        
        # 3. Compute the average chroma vector vertically across time.
        avg_chroma = np.mean(chroma, axis=1)
        
        # Normalize the chroma vector
        chroma_sum = np.sum(avg_chroma)
        if chroma_sum > 0:
            avg_chroma = avg_chroma / chroma_sum
        else:
            return {"key": "Unknown (Noise)", "confidence": 0.0}
            
        # Normalize K-S profiles for dot-product based cosine similarity
        maj_profile = np.array(MAJOR_PROFILE, dtype=float)
        min_profile = np.array(MINOR_PROFILE, dtype=float)
        maj_profile /= np.linalg.norm(maj_profile)
        min_profile /= np.linalg.norm(min_profile)
        
        avg_chroma_norm = avg_chroma / np.linalg.norm(avg_chroma)
        
        best_match = None
        max_corr = -1.0
        
        # 4. Correlate with all 12 musical pitch rotations
        for i in range(12):
            shifted_maj = np.roll(maj_profile, i)
            shifted_min = np.roll(min_profile, i)
            
            # Simple dot product on normalized vectors yields Pearson-like correlation
            corr_maj = np.dot(avg_chroma_norm, shifted_maj)
            corr_min = np.dot(avg_chroma_norm, shifted_min)
            
            if corr_maj > max_corr:
                max_corr = corr_maj
                key_str = f"{PITCH_CLASSES[i]} Major"
                best_match = key_str
            
            if corr_min > max_corr:
                max_corr = corr_min
                key_str = f"{PITCH_CLASSES[i]} Minor"
                best_match = key_str
                
        # Constrain to 0-1 and format
        confidence = max(0.0, float(max_corr))
        
        return {
            "key": best_match,
            "confidence": round(confidence, 4)
        }
    except Exception as e:
        print(f"Key detection error: {str(e)}")
        return {"key": "Error", "confidence": 0.0}

if __name__ == "__main__":
    # Test execution
    res = detect_key("input/example.wav")
    print(res)
