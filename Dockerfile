FROM timpietruskyblibla/runpod-worker-comfy:3.6.0-base

# Install dependencies for CatVTON including unzip
WORKDIR /workspace
RUN apt-get update && apt-get install -y \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and extract ComfyUI-CatVTON
WORKDIR /workspace/ComfyUI/custom_nodes
RUN wget https://github.com/Zheng-Chong/CatVTON/releases/download/ComfyUI/ComfyUI-CatVTON.zip && \
    unzip ComfyUI-CatVTON.zip && \
    rm ComfyUI-CatVTON.zip

# Create workflows directory if it doesn't exist
RUN mkdir -p /workspace/ComfyUI/workflows

# Download workflow file
WORKDIR /workspace/ComfyUI/workflows
RUN wget https://github.com/Zheng-Chong/CatVTON/releases/download/ComfyUI/catvton_workflow.json

# Install Python requirements for CatVTON
WORKDIR /workspace/ComfyUI/custom_nodes/ComfyUI-CatVTON
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Fix any potential permissions issues
WORKDIR /workspace
RUN chmod -R 755 /workspace/ComfyUI

# Return to workspace directory
WORKDIR /workspace