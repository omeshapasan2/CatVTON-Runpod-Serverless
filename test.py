import requests
import json
import time
import base64
import os
from PIL import Image
import io

# Your RunPod API endpoint and token
RUNPOD_API_KEY = "YOUR_RUNPOD_API_KEY"
ENDPOINT_ID = "YOUR_ENDPOINT_ID"
BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

def encode_image_to_base64(image_path):
    """Encode an image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def send_request_to_runpod(person_image_path, garment_image_path):
    """Send a request to RunPod with the person and garment images"""
    # Encode images to base64
    person_image_base64 = encode_image_to_base64(person_image_path)
    garment_image_base64 = encode_image_to_base64(garment_image_path)
    
    # Load the workflow from the JSON file
    with open("catvton_workflow.json", "r") as f:
        workflow_data = json.load(f)
    
    # Update the workflow with the input images
    # Target person image (node 10)
    for node in workflow_data["nodes"]:
        if node["id"] == 10:  # Target Person node
            node["widgets_values"][0] = person_image_base64
        elif node["id"] == 11:  # Reference Garment node
            node["widgets_values"][0] = garment_image_base64
    
    # Prepare the request payload
    payload = {
        "input": {
            "prompt": workflow_data
        }
    }
    
    # Send the request to RunPod
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/run",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def check_status(job_id):
    """Check the status of a submitted job"""
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    response = requests.get(
        f"{BASE_URL}/status/{job_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error checking status: {response.status_code}")
        print(response.text)
        return None

def get_result(job_id):
    """Get the result of a completed job"""
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    response = requests.get(
        f"{BASE_URL}/output/{job_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting result: {response.status_code}")
        print(response.text)
        return None

def save_result_image(result_data, output_path):
    """Save the result image from base64 data"""
    try:
        # Extract the output image data
        output_images = result_data.get("output", {}).get("images", [])
        if not output_images:
            print("No output images found in the result data")
            return False
        
        # Get the first image (assuming that's the try-on result)
        image_data = output_images[0].get("image", "")
        if not image_data:
            print("No image data found")
            return False
        
        # Decode the base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save the image
        image.save(output_path)
        print(f"Result image saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving result image: {e}")
        return False

def main():
    """Main function to orchestrate the process"""
    person_image_path = "person.jpg"
    garment_image_path = "garment.jpg"
    output_path = "result_tryon.jpg"
    
    # Check if input files exist
    if not os.path.exists(person_image_path):
        print(f"Error: Person image not found at {person_image_path}")
        return
    
    if not os.path.exists(garment_image_path):
        print(f"Error: Garment image not found at {garment_image_path}")
        return
    
    print("Sending request to RunPod...")
    response = send_request_to_runpod(person_image_path, garment_image_path)
    
    if not response:
        print("Failed to send request.")
        return
    
    job_id = response.get("id")
    if not job_id:
        print("No job ID received in the response.")
        return
    
    print(f"Job submitted with ID: {job_id}")
    
    # Poll for job status
    status = "IN_QUEUE"
    while status in ["IN_QUEUE", "IN_PROGRESS"]:
        time.sleep(10)  # Wait for 10 seconds before checking status again
        status_response = check_status(job_id)
        if not status_response:
            print("Failed to check job status.")
            return
        
        status = status_response.get("status")
        print(f"Current status: {status}")
    
    if status == "COMPLETED":
        print("Job completed! Fetching results...")
        result = get_result(job_id)
        if result:
            success = save_result_image(result, output_path)
            if success:
                print(f"Virtual try-on successful! Result saved to {output_path}")
            else:
                print("Failed to save result image.")
        else:
            print("Failed to get job result.")
    else:
        print(f"Job failed with status: {status}")

if __name__ == "__main__":
    main()