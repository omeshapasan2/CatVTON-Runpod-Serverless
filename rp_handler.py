import os
import json
import time
import base64
from io import BytesIO
from PIL import Image
import requests

class RPHandler:
    """
    Helper class for handling RunPod serverless functions and common utilities
    """
    
    @staticmethod
    def download_file_from_url(url, save_path=None):
        """
        Download a file from a URL and optionally save it to a path.
        Returns the file content as bytes.
        """
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            content = response.content
            
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(content)
                    
            return content
        except Exception as e:
            print(f"Error downloading from {url}: {e}")
            return None
    
    @staticmethod
    def save_image_from_base64(base64_string, output_path):
        """
        Save a base64 encoded image to a file
        """
        try:
            image_data = base64.b64decode(base64_string)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            return True
        except Exception as e:
            print(f"Error saving base64 image: {e}")
            return False
    
    @staticmethod
    def image_to_base64(image):
        """
        Convert a PIL Image to base64 string
        """
        if isinstance(image, str) and os.path.isfile(image):
            # If image is a file path
            image = Image.open(image)
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    
    @staticmethod
    def base64_to_image(base64_string):
        """
        Convert a base64 string to PIL Image
        """
        try:
            image_data = base64.b64decode(base64_string)
            return Image.open(BytesIO(image_data))
        except Exception as e:
            print(f"Error converting base64 to image: {e}")
            return None
            
    @staticmethod
    def ensure_dir(directory):
        """
        Ensure that a directory exists
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory
