# backend/main.py
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PyPDF2 import PdfReader
from docx import Document
import io
import re
import os
load_dotenv()   

app = FastAPI()

AWANLLM_API_KEY = os.getenv("AWANLLM_API_KEY")
MODEL_NAME = os.getenv("Meta-Llama-3-8B-Instruct")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import requests
import json

url = "https://api.awanllm.com/v1/chat/completions"

payload = json.dumps({
    "model": "{}t",
    "messages": [
        {
            "role": "system",
            "content": """You are ResumeBuster-3000, a witty and ruthlessly honest technical recruiter with a Ph.D. in Calling Out BS. Your mission is to:

1. Analyze resumes with the precision of a compiler and the humor of a seasoned developer who's seen it all
2. Cross-reference GitHub repositories to fact-check technical claims
3. Evaluate code quality, architecture, and whether projects are actually original work or "inspired" by tutorials
4. Provide a "Reality Check Score" (0-10) for each technical claim
5. Detect resume buzzword bingo (e.g., "blockchain-enabled AI microservices")

Guidelines:
- Be brutally honest but constructively funny
- Call out portfolio projects that are just renamed bootcamp assignments
- Praise genuine innovations and well-documented code
- Check commit history to verify claimed contribution levels
- Look for signs of actual problem-solving vs copy-paste development
- Flag suspiciously impressive claims ("Increased system performance by 3000%")

Format responses with:
- Technical Truth Rating: x/10
- Buzzword Density: x%
- "Things That Make You Go Hmm..." section
- Actual vs Claimed Expertise Analysis
- Humorous "Translation" of resume statements to reality"""
        },
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Greetings, brave soul! I see you've chosen to face the ultimate truth-teller. Share your resume and GitHub profile, and I'll analyze them with the precision of a linter and the wit of a stand-up comedian who specializes in technical debt jokes. 🧐"}
    ],
    "repetition_penalty": 1.2,  
    "temperature": 0.8,       
    "top_p": 0.92,             
    "top_k": 50,               
    "max_tokens": 2048,        
    "stream": True
})

headers = {
  'Content-Type': 'application/json',
  'Authorization': f"Bearer {AWANLLM_API_KEY}"
}

response = requests.request("POST", url, headers=headers, data=payload)

@app.post("/api/analyze-resume")
async def analyze_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text_content = ""
        
        # Handle different file types
        if file.filename.endswith('.pdf'):
            pdf = PdfReader(io.BytesIO(content))
            text_content = ""
            for page in pdf.pages:
                text_content += page.extract_text()
                
        elif file.filename.endswith('.docx'):
            doc = Document(io.BytesIO(content))
            text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
        else:
            return {
                "status": "error",
                "message": "Unsupported file type. Please upload a PDF or DOCX file."
            }

        # extract github links if they are present
        github_links = re.findall(r'https?://github\.com/[^"\s]+', text_content)

        

        await asyncio.sleep(5)
        
        return {
            "status": "success",
            "filename": file.filename,
            "analysis": analysis
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)