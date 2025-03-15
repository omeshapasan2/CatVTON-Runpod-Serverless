FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the model handler code
COPY handler.py .
COPY rp_handler.py .

# Add the runpod serverless worker template
RUN mkdir -p /app/inputs /app/outputs /app/cache

# Set environment variables for model caching
ENV TRANSFORMERS_CACHE="/app/cache"
ENV HF_HOME="/app/cache"

# The command to run when the container starts
ENTRYPOINT ["python3", "-u", "handler.py"]