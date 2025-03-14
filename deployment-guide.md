# CatVTON RunPod Serverless Deployment Guide

This guide will walk you through the process of deploying the CatVTON virtual try-on model as a RunPod serverless endpoint.

## Step 1: Prepare Your Repository

1. Create a new repository with the following files:
   - `Dockerfile`
   - `handler.py`
   - `rp_handler.py`
   - `requirements.txt`
   - `README.md`

2. Push the repository to GitHub or another Git hosting service.

## Step 2: Create a RunPod API Key

1. Log in to your RunPod account at [runpod.io](https://www.runpod.io/).
2. Navigate to your account settings by clicking on your profile icon.
3. Select "API Keys" from the menu.
4. Click "Create API Key" and give it a name like "CatVTON Serverless".
5. Copy the generated API key and store it securely.

## Step 3: Create a Hugging Face Token (Optional but Recommended)

1. Sign in to your Hugging Face account at [huggingface.co](https://huggingface.co/).
2. Go to your profile settings and select "Access Tokens".
3. Click "New token" and give it a name like "RunPod CatVTON".
4. Set appropriate permissions (read for public models).
5. Copy the token for use in your RunPod deployment.

## Step 4: Deploy the Serverless Endpoint

### Option 1: Deploy from Docker Hub (Recommended)

1. Build and push your Docker image to Docker Hub:
   ```bash
   docker build -t yourusername/catvton-runpod:latest .
   docker push yourusername/catvton-runpod:latest
   ```

2. In the RunPod dashboard, navigate to "Serverless" > "Templates".
3. Click "New Template" and provide a name like "CatVTON Virtual Try-On".
4. Configure the template with the following settings:
   - Container Image: `yourusername/catvton-runpod:latest`
   - Container Disk: `10GB`
   - Environment Variables:
     - `HUGGING_FACE_HUB_TOKEN`: Your Hugging Face token
   - Container Start Command: Leave blank to use the default from Dockerfile

5. Click "Save Template".

### Option 2: Deploy from GitHub

1. In the RunPod dashboard, navigate to "Serverless" > "Templates".
2. Click "New Template" and provide a name like "CatVTON Virtual Try-On".
3. Configure the template with the following settings:
   - Git Repository URL: Your GitHub repository URL
   - Container Disk: `10GB`
   - Environment Variables:
     - `HUGGING_FACE_HUB_TOKEN`: Your Hugging Face token

4. Click "Save Template".

## Step 5: Create the Endpoint

1. In the RunPod dashboard, navigate to "Serverless" > "Endpoints".
2. Click "New Endpoint" and select your CatVTON template.
3. Configure the endpoint:
   - Network Volume: None (or select a volume if you want to persist data)
   - Min Provisioned Workers: 0 (scale to zero when not in use)
   - Max Workers: 1 (or more if you expect high traffic)
   - Idle Timeout: 5 minutes (adjust based on your needs)
   - GPU Type: Select an appropriate GPU (A4000 or better recommended)
   - vCPU: 4 (minimum recommended)
   - Memory: 16 GB (minimum recommended)

4. Click "Deploy" to create your endpoint.
5. Wait for the endpoint to initialize. This will take some time as the worker needs to download the model weights.

## Step 6: Test Your Endpoint

### Using cURL

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "input": {
      "person_image": "https://example.com/person.jpg",
      "cloth_image": "https://example.com/garment.jpg",
      "cloth_type": "upper",
      "num_inference_steps": 50,
      "guidance_scale": 2.5,
      "seed": 42
    }
  }'
```

### Using the Python Client

Use the provided `runpod_catvton_client.py` script:

```bash
python runpod_catvton_client.py \
  --person "https://example.com/person.jpg" \
  --garment "https://example.com/garment.jpg" \
  --output "result.png" \
  --endpoint "YOUR_ENDPOINT_ID" \
  --api-key "YOUR_API_KEY" \
  --cloth-type "upper"
```

## Troubleshooting

If you encounter issues with your deployment, check the following:

1. **Endpoint Initialization Failed**:
   - Check the logs for any errors during initialization
   - Verify that your Hugging Face token has correct permissions
   - Make sure your GPU has enough memory for the model

2. **Request Timeout**:
   - Increase the request timeout in the RunPod settings
   - Try with a smaller image size

3. **Poor Results**:
   - Make sure your input images are clear and high quality
   - Try adjusting the inference parameters (steps, guidance)
   - Test with different clothing types

4. **Memory Issues**:
   - Increase the memory allocation for your workers
   - Try using a GPU with more VRAM

## Monitoring and Cost Management

1. **Monitor Usage**:
   - Track your usage in the RunPod dashboard
   - Set up alerts for high usage if available

2. **Cost Optimization**:
   - Keep min workers at 0 to only pay for actual usage
   - Adjust idle timeout to balance responsiveness vs. cost
   - Use the appropriate GPU for your needs

## Security Considerations

1. **API Key Security**:
   - Treat your RunPod API key as a secret
   - Rotate your API keys periodically
   - Use scoped API keys when possible

2. **Input Validation**:
   - The handler implements basic input validation
   - Consider adding additional validation if needed

## Updating Your Deployment

To update your serverless deployment:

1. Make changes to your code
2. Build and push a new Docker image with a new tag
3. Update your RunPod template with the new image
4. Redeploy your endpoint

## Support and Resources

- RunPod Documentation: [docs.runpod.io](https://docs.runpod.io)
- RunPod Discord: [discord.gg/runpod](https://discord.gg/runpod)
- Hugging Face CatVTON Model: [huggingface.co/zhengchong/CatVTON](https://huggingface.co/zhengchong/CatVTON)