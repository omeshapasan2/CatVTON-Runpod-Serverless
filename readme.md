# CatVTON RunPod Serverless Worker ...

This repository contains a RunPod serverless worker for the [CatVTON](https://huggingface.co/zhengchong/CatVTON) virtual try-on model by zhengchong. This worker allows you to run the CatVTON model on RunPod's serverless infrastructure.

## Features

- Virtual try-on for clothing items on person images
- Support for upper, lower, and overall clothing types
- Customizable inference parameters
- GPU acceleration via RunPod

## Setup

### Prerequisites

- A RunPod account
- Docker installed on your development machine (for local testing)

### Deployment Steps

1. Create a new serverless template on RunPod
2. Use the Docker image approach with this repository
3. Set the environment variable `HUGGING_FACE_HUB_TOKEN` with your Hugging Face token
4. Deploy the template

## API Usage

### Endpoint

Once deployed, you can access your worker through the RunPod API. The endpoint will be:

```
https://api.runpod.ai/v2/{your-endpoint-id}/run
```

### Request Format

```json
{
  "input": {
    "person_image": "https://url-to-your-person-image.jpg",
    "cloth_image": "https://url-to-your-garment-image.jpg",
    "cloth_type": "upper",
    "num_inference_steps": 50,
    "guidance_scale": 2.5,
    "seed": 42
  }
}
```

Parameters:
- `person_image` (required): URL to the input person image
- `cloth_image` (required): URL to the input garment image
- `cloth_type` (optional): Type of clothing - "upper", "lower", or "overall" (default: "upper")
- `num_inference_steps` (optional): Number of inference steps (default: 50)
- `guidance_scale` (optional): Guidance scale for the model (default: 2.5)
- `seed` (optional): Random seed for reproducibility (default: 42)

### Response Format

```json
{
  "result_image": "base64_encoded_image_data",
  "status": "success"
}
```

In case of an error:

```json
{
  "error": "Error message here"
}
```

## Local Testing

You can test this worker locally using Docker:

```bash
docker build -t catvton-worker .
docker run -p 8000:8000 -e HUGGING_FACE_HUB_TOKEN="your_token_here" catvton-worker
```

## Client Example

Here's a Python code example for calling your RunPod serverless endpoint:

```python
import requests
import json
import base64
from PIL import Image
import io

def call_runpod_catvton(person_image_url, cloth_image_url, runpod_endpoint_id, api_key, 
                       cloth_type="upper", num_steps=50, guidance=2.5, seed=42):
    """Call the RunPod CatVTON endpoint."""
    
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
    
    endpoint_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/run"
    response = requests.post(endpoint_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if "error" in result:
            print(f"Error from RunPod API: {result['error']}")
            return None
            
        # Get the task ID
        task_id = result.get("id")
        status_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/status/{task_id}"
        
        # Poll for completion
        while True:
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            
            if status_data.get("status") == "COMPLETED":
                # Process completed result
                output = status_data.get("output", {})
                if "result_image" in output:
                    # Convert base64 to image
                    img_data = base64.b64decode(output["result_image"])
                    img = Image.open(io.BytesIO(img_data))
                    return img
                return output
            elif status_data.get("status") in ["FAILED", "CANCELLED"]:
                print(f"Task failed: {status_data.get('error')}")
                return None
                
            # Wait before polling again
            time.sleep(2)
    else:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        return None

# Example usage
if __name__ == "__main__":
    # Replace with your actual RunPod endpoint ID and API key
    RUNPOD_ENDPOINT_ID = "your-endpoint-id"
    RUNPOD_API_KEY = "your-api-key"
    
    result_image = call_runpod_catvton(
        person_image_url="https://example.com/person.jpg",
        cloth_image_url="https://example.com/garment.jpg",
        runpod_endpoint_id=RUNPOD_ENDPOINT_ID,
        api_key=RUNPOD_API_KEY,
        cloth_type="upper"
    )
    
    if result_image:
        # Save the result
        result_image.save("result.png")
        print("Successfully generated try-on image and saved to result.png")
```

## References

- [RunPod Serverless Documentation](https://docs.runpod.io/serverless)
- [CatVTON HuggingFace Model](https://huggingface.co/zhengchong/CatVTON)
- [RunPod Worker Handler Documentation](https://docs.runpod.io/serverless/workers/handlers)