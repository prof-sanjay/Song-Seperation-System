# Use an official Python runtime as a parent image
# Python 3.10 is stable for PyTorch, Demucs, and Librosa
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for Audio processing (FFmpeg)
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to cache the pip install step
COPY requirements.txt .

# Install Python dependencies
# We use --no-cache-dir to keep the image lightweight
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories for Demucs processing
RUN mkdir -p /app/input /app/separated

# Copy the rest of the backend application code
COPY app /app/app

# Expose the FastAPI port
EXPOSE 8000

# Command to run the Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
