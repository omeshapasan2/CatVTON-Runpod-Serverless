import requests
import base64
import json
import os
import time
from PIL import Image
import io

class CatVTONClient:
    def __init__(self, endpoint_id="v28ijazx0pm81l", api_key="rpa_YUKU0OP23UN69MBQVHMA7TQ3S2IVI0SU4MM8ZYBX6qmeag"):
        """
        Initialize the CatVTON client.
        
        Args:
            endpoint_id (str): Your RunPod endpoint ID
            api_key (str): Your RunPod API key
        """
        self.endpoint_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        self.status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status"
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Load the workflow template
        with open("catvton_workflow.json", "r") as f:
            self.workflow = json.load(f)
    
    def image_to_base64(self, image_path):
        """Convert an image file to base64 string."""
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    
    def base64_to_image(self, base64_string):
        """Convert a base64 string back to a PIL Image."""
        image_data = base64.b64decode(base64_string)
        return Image.open(io.BytesIO(image_data))
    
    def update_workflow_with_images(self, person_image_path, garment_image_path):
        """
        Update the workflow with the input images.
        
        Args:
            person_image_path (str): Path to the target person image
            garment_image_path (str): Path to the reference garment image
        """
        # Create a modified workflow with base64 images instead of file paths
        modified_workflow = self.workflow.copy()
        
        # Find the LoadImage nodes and replace with LoadImageBase64 nodes
        for node in modified_workflow["nodes"]:
            # Target Person node (ID: 10)
            if node["id"] == 10:
                node["type"] = "LoadImageBase64"
                if "widgets_values" in node:
                    node["widgets_values"] = [
                        self.image_to_base64(person_image_path),
                        "image"
                    ]
            
            # Reference Garment node (ID: 11)
            elif node["id"] == 11:
                node["type"] = "LoadImageBase64"
                if "widgets_values" in node:
                    node["widgets_values"] = [
                        self.image_to_base64(garment_image_path),
                        "image"
                    ]
        
        return modified_workflow
    
    def send_request(self, person_image_path, garment_image_path):
        """
        Send a request to the RunPod endpoint.
        
        Args:
            person_image_path (str): Path to the target person image
            garment_image_path (str): Path to the reference garment image
            
        Returns:
            dict: The response from RunPod
        """
        # Update workflow with the input images
        modified_workflow = self.update_workflow_with_images(person_image_path, garment_image_path)
        
        # Prepare the request payload
        payload = {
            "input": {
                "prompt": {
                    "workflow": modified_workflow,
                    "outputs": {
                        "images": [
                            {"node_id": 18, "field_name": "images"}  # Final output node
                        ]
                    }
                }
            }
        }
        
        # Send the request
        response = requests.post(self.endpoint_url, headers=self.headers, json=payload)
        return response.json()
    
    def check_status(self, job_id):
        """
        Check the status of a job.
        
        Args:
            job_id (str): The job ID returned by the RunPod API
            
        Returns:
            dict: The job status
        """
        response = requests.get(
            f"{self.status_url}/{job_id}", 
            headers=self.headers
        )
        return response.json()
    
    def wait_for_completion(self, job_id, polling_interval=5, timeout=300):
        """
        Wait for a job to complete.
        
        Args:
            job_id (str): The job ID to check
            polling_interval (int): How often to check the status in seconds
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            dict: The final job result or None if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_response = self.check_status(job_id)
            
            if status_response.get("status") == "COMPLETED":
                return status_response.get("output")
            elif status_response.get("status") == "FAILED":
                raise Exception(f"Job failed: {status_response}")
            
            print(f"Job status: {status_response.get('status')}. Waiting {polling_interval} seconds...")
            time.sleep(polling_interval)
        
        raise TimeoutError(f"Job did not complete within {timeout} seconds")
    
    def try_on_garment(self, person_image_path, garment_image_path, output_path="result.png"):
        """
        Complete virtual try-on process from start to finish.
        
        Args:
            person_image_path (str): Path to the target person image
            garment_image_path (str): Path to the reference garment image
            output_path (str): Where to save the resulting image
            
        Returns:
            str: Path to the output image
        """
        # Send the initial request
        print(f"Sending request with target person: {person_image_path} and garment: {garment_image_path}")
        response = self.send_request(person_image_path, garment_image_path)
        
        if "error" in response:
            raise Exception(f"Error sending request: {response['error']}")
        
        job_id = response.get("id")
        if not job_id:
            raise Exception(f"No job ID in response: {response}")
        
        print(f"Job submitted successfully! Job ID: {job_id}")
        print("Waiting for job to complete...")
        
        # Wait for the job to complete
        result = self.wait_for_completion(job_id)
        
        # Process the result
        if result and "images" in result and result["images"]:
            # Get the first output image
            output_image_data = result["images"][0]["image"]
            
            # Remove header if present
            if "," in output_image_data:
                output_image_data = output_image_data.split(",", 1)[1]
            
            # Convert back from base64 to image
            image = self.base64_to_image(output_image_data)
            
            # Save the image
            image.save(output_path)
            print(f"Result saved as {output_path}")
            return output_path
        else:
            raise Exception(f"No images in result: {result}")


# Example usage
if __name__ == "__main__":
    # Initialize the client
    client = CatVTONClient()
    
    # Perform virtual try-on
    try:
        result_path = client.try_on_garment(
            person_image_path="person.jpg",      # Path to your target person (cat) image
            garment_image_path="cloth.jpg"  # Path to your reference garment image
        )
        
        print(f"Try-on completed! Result saved to: {result_path}")
    except Exception as e:
        print(f"Error during try-on process: {e}")