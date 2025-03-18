# CatVTON-Runpod-Serverless

This repository provides a serverless implementation of [CatVTON](https://github.com/Zheng-Chong/CatVTON) using [RunPod](https://www.runpod.io/). The containerized application runs on a GPU-enabled serverless endpoint and processes image inputs for virtual try-on with cats.

## 🚀 Setup Instructions

### 1. Fork the Repository
First, fork this repository:  
👉 [Fork CatVTON-Runpod-Serverless](https://github.com/omeshapasan2/CatVTON-Runpod-Serverless)

### 2. Create a Serverless Endpoint on RunPod
1. Go to [RunPod Console](https://www.runpod.io/console/serverless)
2. Click **Create New Endpoint**
3. Choose **GitHub Repo** as the Custom Source
4. Select your **forked repository**
5. Set the following configurations:
   - **Branch:** `main`
   - **Dockerfile Path:** `Dockerfile`
6. Click **Next**
7. Configure your server:
   - **GPU:** Select any GPU type
   - **Max Workers:** Set based on your needs
   - **Active Workers:** Set to `0` to reduce costs
   - **Idle Timeout:** Configure as per your preference
   - **Execution Timeout:** Configure as per your preference
8. Click **Create Endpoint** and wait until it is ready.

## 📡 Sending Requests with `test.py`

Once your endpoint is active, you can send requests using `test.py`.

### Required Parameters:
- `--api_key` → Your RunPod API Key
- `--endpoint_id` → Your RunPod Endpoint ID
- `--cat` → Path to the cat image
- `--clothing` → Path to the clothing image
- `--async` → (Optional) Run in async mode

### Example Usage:
```bash
python test.py --api_key YOUR_RUNPOD_API_KEY --endpoint_id YOUR_ENDPOINT_ID --cat path/to/cat.png --clothing path/to/clothing.png
```

To run in **asynchronous mode**, use:
```bash
python test.py --api_key YOUR_RUNPOD_API_KEY --endpoint_id YOUR_ENDPOINT_ID --cat path/to/cat.png --clothing path/to/clothing.png --async
```

### Expected Output
- If the request is **synchronous**, the generated image will be saved as `catvton_result.png`.
- If running **asynchronously**, you will receive a Job ID, and the script will poll for the result until completion.

## 🛠 Troubleshooting
- Ensure your **API Key** and **Endpoint ID** are correct.
- Check RunPod's **Logs & Status** if jobs fail.
- Increase **Execution Timeout** if jobs take longer to process.

## 📜 License
This project is based on [CatVTON](https://github.com/Zheng-Chong/CatVTON) and follows its respective license.