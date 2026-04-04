import subprocess
import os

def separate_audio(input_path, output_dir="separated", model="htdemucs_6s"):
    """
    Separates the audio file into multiple stems using Demucs.
    The htdemucs_6s model extracts: vocals, bass, drums, other, piano, and guitar.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting separation for {input_path} using model {model}...")
    
    # Run Demucs CLI
    # '-n' specifies the model, htdemucs_6s supports guitar and piano
    # '-o' specifies the output directory
    command = [
        "python", "-m", "demucs.separate",
        "-n", model,
        "-o", output_dir,
        input_path
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Successfully separated {input_path}")
        print(f"Output saved to {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error during separation: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, "input", "Perfect.mp3")
    output_dir = os.path.join(base_dir, "separated")
    
    if os.path.exists(input_file):
        separate_audio(input_file, output_dir)
    else:
        print(f"Could not find {input_file}")
