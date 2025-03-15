# Use the same base image as the original repo
FROM registry.hf.space/zhengchong-catvton:latest

# Set working directory
WORKDIR /workspace

# Install RunPod Python SDK
RUN pip install runpod pillow

# Clone the CatVTON repo
RUN apt-get update && apt-get install -y git
RUN git clone https://huggingface.co/spaces/zhengchong/CatVTON .

# Copy our handler file
COPY handler.py /workspace/handler.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

ENV HUGGING_FACE_HUB_TOKEN=${HUGGING_FACE_HUB_TOKEN}

# Define the entry point
CMD ["python", "-u", "/workspace/handler.py"]