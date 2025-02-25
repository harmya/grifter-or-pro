# backend/main.py
from dataclasses import dataclass
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from objects import ParsedResumeResponse
from github_verifier import get_github_project_analysis
from resume_parse import parse_resume
import uvicorn
import os
load_dotenv()   

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://grifter.pro",
        "https://grifter.pro",
        "https://www.grifter.pro",
        "http://www.grifter.pro", 
        "http://localhost:3000",
        "https://localhost:3000"
    ],  
    allow_credentials=True,
    allow_methods=["POST"], 
    allow_headers=["*"],
)


@app.post("/api/get-parsed-resume")
async def analyze_resume(file: UploadFile = File(...)):
    contents = await file.read()
    parsed_resume = parse_resume(contents, file.filename, OPENAI_API_KEY)
    await file.close()
    return parsed_resume

@app.post("/api/analyze-resume")
async def analyze_resume(data: ParsedResumeResponse):
    try:   
        if data.found_all_links:
            analysis = get_github_project_analysis(data, GITHUB_TOKEN, OPENAI_API_KEY)     
        else:
            analysis = {
                "name": "None",
                "analysis": "Could not find all links", 
                "code_samples": []
            }

        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False  # Disable reload in production
    )