#!/usr/bin/env python3
import os
import time
import base64
from io import BytesIO
import requests
import runpod
import torch
from PIL import Image
import numpy as np
from diffusers import StableDiffusionControlNetInpaintPipeline
from diffusers.utils import load_image
from transformers import AutoProcessor, CLIPSegProcessor, CLIPSegForImageSegmentation
from rp_handler import RPHandler

# Check if HUGGING_FACE_TOKEN environment variable is set
HF_TOKEN = os.environ.get("HUGGING_FACE_HUB_TOKEN")
if not HF_TOKEN:
    print("Warning: HUGGING_FACE_HUB_TOKEN is not set. Attempting to download models without authentication.")

# Global variables for models
catvton_processor = None
catvton_model = None
pipe = None

def download_image(url):
    """Download an image from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def load_models():
    """Load all required models."""
    global catvton_processor, catvton_model, pipe
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    print("Loading CatVTON model...")
    
    # Load the pipeline from the HuggingFace model
    pipe = StableDiffusionControlNetInpaintPipeline.from_pretrained(
        "zhengchong/CatVTON",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
        token=HF_TOKEN
    )
    
    # Move to GPU if available
    pipe = pipe.to(device)
    
    # Enable memory efficient attention if available
    if device == "cuda":
        pipe.enable_xformers_memory_efficient_attention()
    
    print("All models loaded successfully")

def image_to_base64(image):
    """Convert a PIL Image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def create_blank_white_image(width, height):
    """Create a blank white image with the same dimensions as the input image."""
    return Image.new('RGB', (width, height), 'white')

def handler(job):
    """
    RunPod handler function to process the job.
    """
    try:
        job_input = job["input"]
        
        # Get parameters from job input
        person_image_url = job_input.get("person_image")
        cloth_image_url = job_input.get("cloth_image")
        cloth_type = job_input.get("cloth_type", "upper")  # Default to upper
        num_inference_steps = int(job_input.get("num_inference_steps", 50))
        guidance_scale = float(job_input.get("guidance_scale", 2.5))
        seed = int(job_input.get("seed", 42))
        
        # Validate inputs
        if not person_image_url:
            return {"error": "Missing required parameter: person_image"}
        if not cloth_image_url:
            return {"error": "Missing required parameter: cloth_image"}
        
        # Download images
        person_img = download_image(person_image_url)
        cloth_img = download_image(cloth_image_url)
        
        if person_img is None:
            return {"error": "Failed to download person image"}
        if cloth_img is None:
            return {"error": "Failed to download cloth image"}
        
        # Create blank white image with same dimensions as person image
        blank_white_img = create_blank_white_image(person_img.width, person_img.height)
        
        # Prepare the inputs
        generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed)
        
        # Run CatVTON model for virtual try-on
        result_images = pipe(
            image=person_img,
            mask_image=blank_white_img,  # Use blank white for no masking
            control_image=person_img,    # Use the same person image for control
            prompt=f"a photo of a person wearing {cloth_type} cloth",
            negative_prompt="low quality, bad quality",
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            controlnet_conditioning_scale=1.0,
            generator=generator,
            cloth_image=cloth_img,
            cloth_type=cloth_type,
        ).images
        
        # Convert result image to base64
        if result_images and len(result_images) > 0:
            result_b64 = image_to_base64(result_images[0])
            
            return {
                "result_image": result_b64,
                "status": "success"
            }
        else:
            return {"error": "Failed to generate try-on image"}
            
    except Exception as e:
        return {"error": str(e)}

# Initialize models
load_models()

# Start the RunPod handler
if __name__ == "__main__":
    print("Starting RunPod serverless handler for CatVTON...")
    runpod.serverless.start({"handler": handler})
