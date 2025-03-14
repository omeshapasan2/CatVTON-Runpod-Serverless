#!/usr/bin/env python3
import os
import time
import json
import base64
import argparse
import requests
from io import BytesIO
from PIL import Image

def download_image(url, save_path=None):
    """Download an image from a URL and optionally save it."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        
        if save_path:
            img.save(save_path)
            print(f"Downloaded and saved image to {save_path}")
            
        return img
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def load_local_image(image_path):
    """Load a local image file."""
    try:
        return Image.open(image_path)
    except Exception as e:
        print(f"Error loading image from {image_path}: {e}")
        return None

def call_runpod_catvton(person_image, cloth_image, runpod_endpoint_id, api_key, 
                       cloth_type="upper", num_steps=50, guidance=2.5, seed=42,
                       timeout=300):
    """
    Call the RunPod CatVTON endpoint.
    
    Args:
        person_image: URL or local path to person image
        cloth_image: URL or local path to cloth image
        runpod_endpoint_id: Your RunPod endpoint ID
        api_key: Your RunPod API key
        cloth_type: Type of clothing ("upper", "lower", "overall")
        num_steps: Number of inference steps
        guidance: Guidance scale
        seed: Random seed
        timeout: Maximum time to wait for results in seconds
        
    Returns:
        PIL Image object of the result, or None if failed
    """
    # If inputs are local paths, upload them to temporary storage
    person_image_url = person_image
    cloth_image_url = cloth_image
    
    # If the inputs are local file paths, we need to upload them somewhere
    if os.path.isfile(person_image):
        # For demonstration, we'll use a free image hosting service
        # In production, use a more reliable service or your own storage
        print(f"Uploading {person_image} to temporary storage...")
        try:
            from imgbb_upload import imgbb_upload
            person_image_url = imgbb_upload(person_image)
            print(f"Uploaded person image: {person_image_url}")
        except ImportError:
            print("Error: Please install imgbb_upload using 'pip install imgbb-upload' to upload local files")
            return None
        except Exception as e:
            print(f"Error uploading person image: {e}")
            return None
            
    if os.path.isfile(cloth_image):
        print(f"Uploading {cloth_image} to temporary storage...")
        try:
            from imgbb_upload import imgbb_upload
            cloth_image_url = imgbb_upload(cloth_image)
            print(f"Uploaded cloth image: {cloth_image_url}")
        except ImportError:
            print("Error: Please install imgbb_upload using 'pip install imgbb-upload' to upload local files")
            return None
        except Exception as e:
            print(f"Error uploading cloth image: {e}")
            return None
    
    # Prepare the payload
    payload = {
        "input": {
            "person_image": person_image_url,
            "cloth_image": cloth_image_url,
            "cloth_type": cloth_type,
            "num_inference_steps": num_steps,
            "guidance_scale": guidance,
            "seed": seed
        }
    }
    
    # Make the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"Sending request to RunPod serverless endpoint...")
    endpoint_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/run"
    response = requests.post(endpoint_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if "error" in result:
            print(f"Error from RunPod API: {result['error']}")
            return None
            
        # Get the task ID
        task_id = result.get("id")
        print(f"Task submitted successfully. Task ID: {task_id}")
        status_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/status/{task_id}"
        
        # Poll for completion
        start_time = time.time()
        print("Waiting for results...")
        
        while time.time() - start_time < timeout:
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            
            if status_data.get("status") == "COMPLETED":
                print("Task completed successfully!")
                # Process completed result
                output = status_data.get("output", {})
                if "result_image" in output:
                    # Convert base64 to image
                    img_data = base64.b64decode(output["result_image"])
                    img = Image.open(BytesIO(img_data))
                    return img
                return output
            elif status_data.get("status") in ["FAILED", "CANCELLED"]:
                print(f"Task failed: {status_data.get('error')}")
                return None
                
            # Print status and wait before polling again
            if "status" in status_data:
                print(f"Current status: {status_data['status']}")
            time.sleep(5)
            
        print(f"Timeout after waiting {timeout} seconds")
        return None
    else:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        return None

def main():
    parser = argparse.ArgumentParser(description="RunPod CatVTON Client")
    parser.add_argument("--person", required=True, help="URL or path to person image")
    parser.add_argument("--garment", required=True, help="URL or path to garment image")
    parser.add_argument("--output", default="result.png", help="Output image path (default: result.png)")
    parser.add_argument("--endpoint", required=True, help="RunPod endpoint ID")
    parser.add_argument("--api-key", required=True, help="RunPod API key")
    parser.add_argument("--cloth-type", default="upper", choices=["upper", "lower", "overall"], 
                        help="Type of clothing (default: upper)")
    parser.add_argument("--steps", type=int, default=50, help="Number of inference steps (default: 50)")
    parser.add_argument("--guidance", type=float, default=2.5, help="Guidance scale (default: 2.5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (default: 300)")
    
    args = parser.parse_args()
    
    result_image = call_runpod_catvton(
        person_image=args.person,
        cloth_image=args.garment,
        runpod_endpoint_id=args.endpoint,
        api_key=args.api_key,
        cloth_type=args.cloth_type,
        num_steps=args.steps,
        guidance=args.guidance,
        seed=args.seed,
        timeout=args.timeout
    )
    
    if result_image:
        # Save the result
        result_image.save(args.output)
        print(f"Successfully generated try-on image and saved to {args.output}")
        return 0
    else:
        print("Failed to generate try-on image")
        return 1

if __name__ == "__main__":
    exit(main())
