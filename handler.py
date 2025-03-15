import os
import runpod
import base64
import requests
import traceback
from io import BytesIO
from PIL import Image
import gradio as gr
from tempfile import NamedTemporaryFile

# Import the CatVTON app
spec = importlib.util.spec_from_file_location("app", "/workspace/app.py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app"] = app_module
spec.loader.exec_module(app_module)

# Initialize the model
model = None

def init_model():
    global model
    if model is None:
        print("Initializing CatVTON model...")
        # Create an instance of the main app class
        # This might need to be adjusted based on how the app.py file is structured
        try:
            if hasattr(app_module, "CatVTONInference"):
                model = app_module.CatVTONInference()
            else:
                # If there's no specific class, try to get the model from app variables
                model = app_module
            print("Model initialized successfully")
        except Exception as e:
            print(f"Error initializing model: {str(e)}")
            print(traceback.format_exc())
            raise
    return model

def create_blank_white_png_like(image_bytes):
    """
    Creates a blank white PNG with the same dimensions as the input image.
    
    Args:
        image_bytes (bytes): Input image as bytes
    
    Returns:
        tuple: (original_png_bytes, blank_white_png_bytes)
    """
    try:
        # Open the image bytes
        img = Image.open(BytesIO(image_bytes))
        
        # Convert to PNG in memory
        png_buffer = BytesIO()
        img.save(png_buffer, format='PNG')
        png_bytes = png_buffer.getvalue()
        
        # Get dimensions
        width, height = img.size
        
        # Create blank white image
        blank_image = Image.new('RGB', (width, height), 'white')
        blank_buffer = BytesIO()
        blank_image.save(blank_buffer, format='PNG')
        blank_bytes = blank_buffer.getvalue()
        
        return png_bytes, blank_bytes
    except Exception as e:
        print(f"Error creating blank image: {e}")
        return None, None

def image_to_base64(image_bytes):
    """Convert image bytes to base64 string"""
    return base64.b64encode(image_bytes).decode('utf-8')

def base64_to_image(base64_string):
    """Convert base64 string to image bytes"""
    return base64.b64decode(base64_string)

def handler(event):
    """
    RunPod handler function for CatVTON.
    
    Expected input format:
    {
        "input": {
            "person_image": "base64_encoded_string",
            "cloth_image": "base64_encoded_string",
            "cloth_type": "upper", # or "lower", "overall"
            "num_inference_steps": 50,
            "guidance_scale": 2.5,
            "seed": 42
        }
    }
    """
    try:
        # Initialize model
        model = init_model()
        
        # Get input data
        input_data = event["input"]
        
        # Get and decode the images
        person_image_bytes = base64_to_image(input_data["person_image"])
        cloth_image_bytes = base64_to_image(input_data["cloth_image"])
        
        # Create blank white PNG with same dimensions as person image
        person_png_bytes, blank_white_bytes = create_blank_white_png_like(person_image_bytes)
        
        # Save temporary files to pass to the model
        with NamedTemporaryFile(suffix=".png", delete=False) as person_file, \
             NamedTemporaryFile(suffix=".png", delete=False) as blank_file, \
             NamedTemporaryFile(suffix=".png", delete=False) as garment_file:
            
            person_file.write(person_png_bytes)
            blank_file.write(blank_white_bytes)
            garment_file.write(cloth_image_bytes)
            
            person_path = person_file.name
            blank_path = blank_file.name
            garment_path = garment_file.name
        
        # Extract other parameters
        cloth_type = input_data.get("cloth_type", "upper")
        num_inference_steps = input_data.get("num_inference_steps", 50)
        guidance_scale = input_data.get("guidance_scale", 2.5)
        seed = input_data.get("seed", 42)
        
        # Create a function equivalent to what the gradio client is calling
        result = model.process_images(
            person_image={
                "background": person_path,
                "layers": [blank_path],
                "composite": person_path
            },
            cloth_image=garment_path,
            cloth_type=cloth_type,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=seed,
            show_type="result only"
        )
        
        # Convert result to base64
        if isinstance(result, str) and os.path.exists(result):
            # If result is a file path
            with open(result, "rb") as f:
                result_bytes = f.read()
        elif isinstance(result, Image.Image):
            # If result is a PIL Image
            buffer = BytesIO()
            result.save(buffer, format="PNG")
            result_bytes = buffer.getvalue()
        else:
            # Handle other result types as needed
            raise ValueError(f"Unexpected result type: {type(result)}")
        
        result_base64 = image_to_base64(result_bytes)
        
        # Clean up temporary files
        for file_path in [person_path, blank_path, garment_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return {
            "output": {
                "result_image": result_base64
            }
        }
        
    except Exception as e:
        error_message = f"Error processing request: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {
            "error": error_message
        }

# Start the RunPod serverless handler
runpod.serverless.start({"handler": handler})