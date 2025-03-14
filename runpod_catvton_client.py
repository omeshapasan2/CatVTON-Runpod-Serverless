#!/usr/bin/env python3
import os
import time
import json
import base64
import argparse
import requests
from io import BytesIO
from PIL import Image

# Choose one of these image handling methods:
# METHOD 1: Using imgbb with API key (install with `pip install imgbb`)
# METHOD 2: Direct base64 encoding (no external dependencies)

# --------------------------
# METHOD 1: imgbb Upload (requires API key)
# --------------------------
# def upload_to_imgbb(image_path, api_key):
#     """Upload image to imgbb.com and return URL"""
#     try:
#         from imgbb import imgbb
#         response = imgbb.upload(image_path, api_key)
#         return response['data']['url']
#     except Exception as e:
#         print(f"Image upload failed: {e}")
#         return None

# --------------------------
# METHOD 2: Base64 Encoding
# --------------------------
def image_to_base64(image_path):
    """Convert local image to base64 data URI"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/{image_path.split('.')[-1]};base64,{encoded_string}"
    except Exception as e:
        print(f"Base64 encoding failed: {e}")
        return None

def call_runpod_catvton(person_image, cloth_image, runpod_endpoint_id, api_key,
                       cloth_type="upper", num_steps=50, guidance=2.5, seed=42,
                       timeout=300):
    """
    Call the RunPod CatVTON endpoint.
    """
    # Handle local images
    if os.path.isfile(person_image):
        # For METHOD 1 (imgbb):
        # person_image_url = upload_to_imgbb(person_image, "YOUR_IMGBB_API_KEY")
        
        # For METHOD 2 (base64):
        person_image_url = image_to_base64(person_image)
        
        if not person_image_url:
            return None

    if os.path.isfile(cloth_image):
        # For METHOD 1 (imgbb):
        # cloth_image_url = upload_to_imgbb(cloth_image, "YOUR_IMGBB_API_KEY")
        
        # For METHOD 2 (base64):
        cloth_image_url = image_to_base64(cloth_image)
        
        if not cloth_image_url:
            return None

    # Prepare payload
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

    # API headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # RunPod endpoint URLs
    endpoint_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/run"
    print(f"Sending request to RunPod endpoint...")

    try:
        response = requests.post(endpoint_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            print(f"API Error: {result['error']}")
            return None

        task_id = result.get("id")
        print(f"Task ID: {task_id}")
        status_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/status/{task_id}"

        # Poll for results
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()

            if status_data.get("status") == "COMPLETED":
                output = status_data.get("output", {})
                if "result_image" in output:
                    img_data = base64.b64decode(output["result_image"])
                    return Image.open(BytesIO(img_data))
                return None
            elif status_data.get("status") in ["FAILED", "CANCELLED"]:
                print(f"Task failed: {status_data.get('error')}")
                return None
            
            print(f"Status: {status_data.get('status')}")
            time.sleep(5)

        print("Timeout reached")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="RunPod CatVTON Client")
    parser.add_argument("--person", required=True, help="Path/URL to person image")
    parser.add_argument("--garment", required=True, help="Path/URL to garment image")
    parser.add_argument("--output", default="result.png", help="Output image path")
    parser.add_argument("--endpoint", required=True, help="RunPod endpoint ID")
    parser.add_argument("--api-key", required=True, help="RunPod API key")
    parser.add_argument("--cloth-type", default="upper", choices=["upper", "lower", "overall"])
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--guidance", type=float, default=2.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=int, default=300)

    args = parser.parse_args()

    result = call_runpod_catvton(
        args.person,
        args.garment,
        args.endpoint,
        args.api_key,
        cloth_type=args.cloth_type,
        num_steps=args.steps,
        guidance=args.guidance,
        seed=args.seed,
        timeout=args.timeout
    )

    if result:
        result.save(args.output)
        print(f"Saved result to {args.output}")
        return 0
    else:
        print("Failed to generate image")
        return 1

if __name__ == "__main__":
    exit(main())