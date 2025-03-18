import requests
import base64
import json
import os
import argparse
import time
from PIL import Image
from io import BytesIO

def image_to_base64(image_path):
    """Convert an image to base64 encoding"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def base64_to_image(base64_string, output_path):
    """Convert a base64 string to an image and save it"""
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    image.save(output_path)
    print(f"Image saved to {output_path}")
    return image

def load_workflow(json_path="catvton_workflow.json"):
    """Load the workflow from the JSON file"""
    with open(json_path, 'r') as f:
        return json.load(f)

def run_catvton(api_key, endpoint_id, cat_image_path, clothing_image_path, sync=True):
    """Run the CatVTON workflow on RunPod"""
    # Load workflow
    workflow = load_workflow()
    
    # Convert images to base64
    cat_base64 = image_to_base64(cat_image_path)
    clothing_base64 = image_to_base64(clothing_image_path)
    
    # Prepare API request
    url = f"https://api.runpod.ai/v2/{endpoint_id}/{'runsync' if sync else 'run'}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Create payload
    payload = {
        "input": {
            "workflow": workflow,
            "images": [
                {
                    "name": "cat.png",
                    "image": cat_base64
                },
                {
                    "name": "clothing.png",
                    "image": clothing_base64
                }
            ]
        }
    }
    
    # Send request
    print(f"Sending request to RunPod endpoint {endpoint_id}...")
    response = requests.post(url, headers=headers, json=payload)
    
    # Handle response
    if response.status_code == 200:
        result = response.json()
        print(f"Request successful! Job ID: {result.get('id')}")
        
        if sync:
            # If synchronous, we have the result already
            output_data = result.get('output', {})
            if output_data.get('status') == 'success':
                # Check if the result is a URL or base64
                message = output_data.get('message', '')
                if message.startswith('http'):
                    print(f"Generated image URL: {message}")
                    # Download image from URL
                    img_response = requests.get(message)
                    if img_response.status_code == 200:
                        output_path = "catvton_result.png"
                        with open(output_path, "wb") as f:
                            f.write(img_response.content)
                        print(f"Image downloaded to {output_path}")
                else:
                    # Assume it's base64
                    output_path = "catvton_result.png"
                    base64_to_image(message, output_path)
            else:
                print(f"Error: {output_data.get('message')}")
        else:
            # If asynchronous, we need to poll for the result
            job_id = result.get('id')
            print(f"Job submitted (ID: {job_id}). Check status at https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}")
            
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def check_job_status(api_key, endpoint_id, job_id):
    """Check the status of an asynchronous job"""
    url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error checking status: {response.status_code}")
        print(response.text)
        return None

def poll_until_complete(api_key, endpoint_id, job_id, interval=5, max_attempts=60):
    """Poll the job status until it completes or fails"""
    attempts = 0
    while attempts < max_attempts:
        status_data = check_job_status(api_key, endpoint_id, job_id)
        if not status_data:
            return None
        
        status = status_data.get('status')
        if status == 'COMPLETED':
            output_data = status_data.get('output', {})
            if output_data.get('status') == 'success':
                message = output_data.get('message', '')
                if message.startswith('http'):
                    print(f"Generated image URL: {message}")
                    # Download image from URL
                    img_response = requests.get(message)
                    if img_response.status_code == 200:
                        output_path = "catvton_result.png"
                        with open(output_path, "wb") as f:
                            f.write(img_response.content)
                        print(f"Image downloaded to {output_path}")
                else:
                    # Assume it's base64
                    output_path = "catvton_result.png"
                    base64_to_image(message, output_path)
            return status_data
        elif status == 'FAILED':
            print(f"Job failed: {status_data.get('error')}")
            return status_data
        
        print(f"Job status: {status}, waiting {interval} seconds...")
        time.sleep(interval)
        attempts += 1
    
    print(f"Reached maximum polling attempts ({max_attempts})")
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CatVTON on RunPod")
    parser.add_argument("--api_key", help="RunPod API key", required=True)
    parser.add_argument("--endpoint_id", help="RunPod endpoint ID", required=True)
    parser.add_argument("--cat", help="Path to cat image", required=True)
    parser.add_argument("--clothing", help="Path to clothing image", required=True)
    parser.add_argument("--async", dest="async_mode", action="store_true", help="Run in asynchronous mode")
    
    args = parser.parse_args()
    
    if args.async_mode:
        # Run asynchronously
        result = run_catvton(args.api_key, args.endpoint_id, args.cat, args.clothing, sync=False)
        if result and 'id' in result:
            job_id = result['id']
            poll_until_complete(args.api_key, args.endpoint_id, job_id)
    else:
        # Run synchronously
        run_catvton(args.api_key, args.endpoint_id, args.cat, args.clothing, sync=True)