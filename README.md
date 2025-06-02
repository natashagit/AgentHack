# Building your very own agent

Create your own agents to do repetitive tasks without writing a single line of code. Just upload a video of what you want it to do, and our AI will handle the rest!

## Video Task Automation API

This FastAPI application processes video recordings of tasks and uses Google's Gemini 2.5 Pro to generate step-by-step prompts for automation. The generated prompts are then executed using browser-use for task automation.

[Visit the website](https://natashagit.github.io/AgentHack/)

## Prerequisites

- Python 3.8 or higher
- Google Cloud API key with Gemini API access
- A modern web browser (for browser-use automation)

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## Running the Application

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /process-video
Upload a video file to process and automate tasks.

**Request:**
- Content-Type: multipart/form-data
- Body: video file (MP4 format)

**Response:**
```json
{
    "prompt": "Generated step-by-step prompt",
    "status": "success"
}
```

## Usage Example

You can test the API using curl:
```bash
curl -X POST -F "video=@path/to/your/video.mp4" http://localhost:8000/process-video
```

Or using Python requests:
```python
import requests

url = "http://localhost:8000/process-video"
files = {"video": open("path/to/your/video.mp4", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

## Notes

- The video should be in MP4 format
- The video should clearly show the tasks being performed
- The generated prompt will be automatically executed using browser-use
- Make sure you have proper permissions and access rights for the tasks being automated 
