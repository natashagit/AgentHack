import os
import tempfile
import asyncio
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.genai as genai
from dotenv import load_dotenv
from browser_use import Agent
from langchain_openai import ChatOpenAI
import time

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

client = genai.Client(api_key=GOOGLE_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def wait_for_file_processing(file):
    """Wait for file to be in ACTIVE state"""
    max_retries = 120  # Increased to 120 retries (10 minutes)
    retry_delay = 5  # 5 seconds between retries
    
    print("\n=== Starting File Processing Check ===")
    print(f"File object: {file}")
    print(f"File type: {type(file)}")
    print(f"File attributes: {dir(file)}")
    
    # Check if file has a name attribute
    if not hasattr(file, 'name'):
        print("Error: File object has no 'name' attribute")
        return False
        
    # Get initial file status
    try:
        file_status = client.files.get(name=file.name)
        print(f"Initial file status: {file_status}")
        print(f"File status type: {type(file_status)}")
        print(f"File status attributes: {dir(file_status)}")
        
        # Check if there's any error in the initial status
        if hasattr(file_status, 'error') and file_status.error:
            print(f"Error in file status: {file_status.error}")
            return False
            
    except Exception as e:
        print(f"Error getting initial file status: {str(e)}")
        return False
    
    for attempt in range(max_retries):
        try:
            # Get fresh file status on each attempt
            current_status = client.files.get(name=file.name)
            file_state = current_status.state
            
            print(f"\nAttempt {attempt + 1}/{max_retries}")
            print(f"Current file state: {file_state}")
            print(f"Time elapsed: {(attempt + 1) * retry_delay} seconds")
            
            # Check for any error in the current status
            if hasattr(current_status, 'error') and current_status.error:
                print(f"Error in file status: {current_status.error}")
                return False
            
            if file_state == "ACTIVE":
                print("✓ File is now ACTIVE and ready for use")
                return True
            elif file_state == "FAILED":
                print("✗ File processing failed")
                if hasattr(current_status, 'error'):
                    print(f"Failure reason: {current_status.error}")
                return False
            elif file_state == "PROCESSING":
                print("⟳ File is still processing...")
                # Check if there's any progress information
                if hasattr(current_status, 'video_metadata'):
                    print(f"Processing metadata: "
                          f"{current_status.video_metadata}")
            else:
                print(f"! Unexpected file state: {file_state}")
            
            time.sleep(retry_delay)
        except Exception as e:
            print(f"Error checking file state: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {dir(e)}")
            time.sleep(retry_delay)
    
    print("\n=== File Processing Timed Out ===")
    print(f"Total time waited: {max_retries * retry_delay} seconds")
    return False

async def run_browser_agent(description):
    """Run the browser agent with the video description"""
    agent = Agent(
        task=description,
        llm=ChatOpenAI(model="gpt-4o")
    )
    return await agent.run()

@app.post("/process-video")
async def process_video(video: UploadFile):
    try:
        print("\n=== Starting Video Processing ===")
        print(f"Received video: {video.filename}")
        print(f"Content type: {video.content_type}")
        
        # Create a temporary file to store the uploaded video
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp4"
        ) as temp_file:
            content = await video.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            print(f"Temporary file created at: {temp_file_path}")
            print(f"File size: {len(content)} bytes")

        # Upload the video to Gemini
        try:
            print("\n=== Uploading to Gemini ===")
            # Check if the file exists and is readable
            if not os.path.exists(temp_file_path):
                raise Exception("Temporary file not found")
            
            file_size = os.path.getsize(temp_file_path)
            print(f"File size before upload: {file_size} bytes")
            
            # Upload the file
            file = client.files.upload(file=temp_file_path)
            print("File uploaded successfully")
            print(f"Uploaded file object: {file}")
            print(f"Uploaded file type: {type(file)}")
            print(f"Uploaded file attributes: {dir(file)}")
            
            # Wait for file to be processed
            if not wait_for_file_processing(file):
                raise HTTPException(
                    status_code=400,
                    detail="File processing timeout. Please try again."
                )
            
            # Generate content using the video
            prompt = (
                "Analyze this video and provide a detailed, step-by-step "
                "description of all actions performed. Focus on exact "
                "timestamps, UI elements, and user interactions. Format the "
                "output as a series of browser automation instructions that "
                "can be used to replicate these actions. Include specific "
                "details about elements to click, text to enter, and any "
                "navigation steps."
            )
            print("\n=== Generating Content ===")
            print("Using model: gemini-2.5-pro-preview-05-06")
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-pro-preview-05-06",
                    contents=[file, prompt]
                )
                print("Content generated successfully")
                
                # Clean up the temporary file
                os.unlink(temp_file_path)
                print("Temporary file cleaned up")
                
                # Run the browser agent with the generated description
                print("\n=== Running Browser Agent ===")
                browser_result = await run_browser_agent(response.text)
                
                return {
                    "description": response.text,
                    "browser_result": browser_result
                }
                
            except Exception as gen_error:
                print("\n=== Content Generation Error ===")
                print(f"Error type: {type(gen_error)}")
                print(f"Error details: {str(gen_error)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Error generating content: {str(gen_error)}"
                )
            
        except Exception as e:
            # Clean up the temporary file in case of error
            os.unlink(temp_file_path)
            print("\n=== Upload Error ===")
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
            
    except Exception as e:
        print("\n=== Unexpected Error ===")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 