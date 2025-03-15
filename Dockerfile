# Use a base image with Python and CUDA
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Set working directory
WORKDIR /workspace

# Install required packages
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install RunPod Python SDK
RUN pip3 install runpod pillow requests gradio-client

# Clone the space repository directly (this is the key change)
RUN git clone https://huggingface.co/spaces/zhengchong/CatVTON .

# Install the requirements
RUN pip3 install -r requirements.txt

# Copy our handler file
COPY handler.py /workspace/handler.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

ENV HUGGING_FACE_HUB_TOKEN=${HUGGING_FACE_HUB_TOKEN}

# Expose port for Gradio (if needed)
EXPOSE 7860

# Define the entry point
CMD ["python3", "-u", "/workspace/handler.py"]