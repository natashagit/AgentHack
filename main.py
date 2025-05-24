import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
from browser_use import BrowserUse
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Video Task Automation API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro-vision')

class TaskResponse(BaseModel):
    prompt: str
    status: str

@app.post("/process-video", response_model=TaskResponse)
async def process_video(video: UploadFile = File(...)):
    try:
        # Save the uploaded video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            content = await video.read()
            temp_video.write(content)
            temp_video_path = temp_video.name

        # Process video with Gemini
        prompt = (
            "Analyze this video and create a detailed step-by-step prompt of the tasks "
            "being performed. Focus on the sequence of actions and any specific details "
            "that would be important for automation. Format the output as a clear, "
            "sequential list of steps."
        )

        # Generate task prompt using Gemini
        response = model.generate_content([prompt, temp_video_path])
        task_prompt = response.text

        # Clean up temporary file
        os.unlink(temp_video_path)

        # Initialize browser-use with the generated prompt
        browser = BrowserUse()
        browser.execute(task_prompt)

        return TaskResponse(
            prompt=task_prompt,
            status="success"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Video Task Automation API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 