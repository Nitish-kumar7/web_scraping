from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import requests
from pydantic import BaseModel
from instagram_scraper import InstagramScraper

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

# Initialize Instagram scraper
instagram_scraper = InstagramScraper(rate_limit=5)

class InstagramProfileRequest(BaseModel):
    username: str

@app.get("/")
async def root():
    return {"message": "Candidate Data Analyzer API"}

@app.get("/github/{username}")
async def get_github_profile(username: str, api_key: str = Depends(get_api_key)):
    try:
        logger.info(f"Fetching GitHub profile for user: {username}")
        response = requests.get(f"https://api.github.com/users/{username}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching GitHub profile: {str(e)}")
        raise HTTPException(status_code=404, detail=f"GitHub profile not found: {str(e)}")

@app.get("/instagram/{username}")
async def get_instagram_profile(username: str):
    """
    Fetch Instagram profile data for a given username.
    """
    try:
        profile_data = instagram_scraper.scrape_profile(username)
        
        if 'error' in profile_data:
            status_code = 404 if 'Profile not found' in profile_data['error'] else 500
            raise HTTPException(
                status_code=status_code,
                detail=profile_data['error']
            )
            
        return profile_data
    except Exception as e:
        logger.error(f"Error scraping Instagram profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping Instagram profile: {str(e)}"
        )

@app.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    try:
        logger.info(f"Processing resume upload: {file.filename}")
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        
        # Save the uploaded file
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # TODO: Implement PDF parsing logic here
        # For now, return a simple response
        return {
            "message": "Resume uploaded successfully",
            "filename": file.filename,
            "file_path": file_path
        }
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing resume: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 