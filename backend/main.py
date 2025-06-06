from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from typing import Optional
import uvicorn
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

from github_extractor import fetch_github_profile
from resume_parser import parse_resume

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Only use console logging for now
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Candidate Data Analyzer",
    description="API for analyzing candidate data from GitHub and Resumes",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

@app.get("/")
async def root():
    return {"message": "Candidate Data Analyzer API"}

@app.get("/github/{username}")
async def get_github_profile(username: str, api_key: str = Depends(get_api_key)):
    try:
        logger.info(f"Fetching GitHub profile for user: {username}")
        profile_data = fetch_github_profile(username)
        return profile_data
    except Exception as e:
        logger.error(f"Error fetching GitHub profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    try:
        logger.info(f"Processing resume upload: {file.filename}")
        content = await file.read()
        parsed_data = parse_resume(content, file.filename)
        return parsed_data
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 