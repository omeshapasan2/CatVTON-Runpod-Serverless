import os
import time
import base64
import requests
import argparse
from PIL import Image
from io import BytesIO

def encode_image_to_base64(image_path):
    """Convert an image file to base64 encoded string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def save_base64_to_image(base64_string, output_path):
    """Convert base64 string to image and save to file"""
    image_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as f:
        f.write(image_data)
    print(f"Saved output image to {output_path}")

def run_inference(person_image_path, garment_image_path, api_key, endpoint_id, 
                  cloth_type="upper", num_steps=50, guidance=2.5, seed=42, output_path="output.png"):
    """
    Run inference on RunPod serverless endpoint
    
    Args:
        person_image_path (str): Path to the person image
        garment_image_path (str): Path to the garment image
        api_key (str): RunPod API key
        endpoint_id (str): RunPod endpoint ID
        cloth_type (str): Type of clothing ("upper", "lower", "overall")
        num_steps (int): Number of inference steps
        guidance (float): Guidance scale
        seed (int): Random seed
        output_path (str): Path to save the output image
    """
    # Encode images to base64
    person_base64 = encode_image_to_base64(person_image_path)
    garment_base64 = encode_image_to_base64(garment_image_path)
    
    # Create request payload
    payload = {
        "input": {
            "person_image": person_base64,
            "cloth_image": garment_base64,
            "cloth_type": cloth_type,
            "num_inference_steps": num_steps,
            "guidance_scale": guidance,
            "seed": seed
        }
    }
    
    # API endpoint
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Submit job
    print("Submitting job to RunPod...")
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response.status_code != 200:
        print(f"Error submitting job: {response_data}")
        return
    
    job_id = response_data.get("id")
    if not job_id:
        print(f"Failed to get job ID: {response_data}")
        return
    
    print(f"Job submitted successfully! Job ID: {job_id}")
    
    # Poll for results
    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    while True:
        print("Checking job status...")
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        
        if status_data.get("status") == "COMPLETED":
            print("Job completed!")
            break
        elif status_data.get("status") == "FAILED":
            print(f"Job failed: {status_data}")
            return
        
        print("Job still processing, waiting 5 seconds...")
        time.sleep(5)
    
    # Get results
    output = status_data.get("output", {})
    if "error" in output:
        print(f"Error in processing: {output['error']}")
        return
    
    result_image = output.get("output", {}).get("result_image")
    if not result_image:
        print(f"No result image found in response: {output}")
        return
    
    # Save the result image
    save_base64_to_image(result_image, output_path)
    print("Process completed successfully!")

def main():
    parser = argparse.ArgumentParser(description="RunPod CatVTON Client")
    parser.add_argument("--person", required=True, help="Path to person image")
    parser.add_argument("--garment", required=True, help="Path to garment image")
    parser.add_argument("--api-key", required=True, help="RunPod API key")
    parser.add_argument("--endpoint-id", required=True, help="RunPod endpoint ID")
    parser.add_argument("--cloth-type", default="upper", choices=["upper", "lower", "overall"],
                        help="Type of clothing")
    parser.add_argument("--steps", type=int, default=50, help="Number of inference steps")
    parser.add_argument("--guidance", type=float, default=2.5, help="Guidance scale")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")