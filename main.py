"""
Resume Screener - FastAPI Backend
Uses OpenAI to analyze resumes against a job description
"""

import os
import json
import tempfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="Resume Screener", version="1.0.0")

# Allow requests from the frontend (important for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client (reads OPENAI_API_KEY from environment)
client = OpenAI()


# ─── Helper Functions ─────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file given its bytes."""
    text = ""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    finally:
        os.unlink(tmp_path)  # Clean up temp file

    return text.strip()


def analyze_resume_with_openai(
    resume_text: str,
    job_description: str,
    candidate_name: str,
) -> dict:
    """
    Send resume + JD to OpenAI and get back a structured score + reason.
    We ask for JSON output so we can easily parse it.
    """

    system_prompt = """You are an expert technical recruiter. 
Analyze the provided resume against the job description and return ONLY valid JSON.
No extra text, no markdown fences — just the raw JSON object."""

    user_prompt = f"""
Job Description:
{job_description}

---

Resume ({candidate_name}):
{resume_text[:4000]}  # Truncate to stay within token limits

---

Return this exact JSON structure:
{{
  "score": <integer 0-100>,
  "summary": "<2-3 sentence summary of the candidate>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "gaps": ["<gap 1>", "<gap 2>"],
  "recommendation": "<Highly Recommended | Recommended | Maybe | Not Recommended>"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",   # Fast + cheap, great for prototypes
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,       # Lower = more consistent/factual output
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()

    # Parse the JSON OpenAI returned
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if model adds extra text despite instructions
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        result = json.loads(match.group()) if match else {}

    return result


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML file."""
    html_path = Path(__file__).parent / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return HTMLResponse(content=html_path.read_text())


@app.post("/screen")
async def screen_resumes(
    job_description: str = Form(...),        # Text field from form
    resumes: List[UploadFile] = File(...),   # Multiple PDF uploads
):
    """
    Main endpoint: accepts PDFs + job description, returns ranked candidates.
    """

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")

    if not resumes:
        raise HTTPException(status_code=400, detail="Please upload at least one resume.")

    results = []

    for resume_file in resumes:
        # Validate file type
        if not resume_file.filename.lower().endswith(".pdf"):
            results.append({
                "name": resume_file.filename,
                "error": "Only PDF files are supported.",
                "score": 0,
            })
            continue

        try:
            # Read the uploaded file bytes
            file_bytes = await resume_file.read()

            # Extract text from PDF
            resume_text = extract_text_from_pdf(file_bytes)

            if not resume_text:
                results.append({
                    "name": resume_file.filename,
                    "error": "Could not extract text. Is the PDF scanned/image-based?",
                    "score": 0,
                })
                continue

            # Analyze with OpenAI
            candidate_name = resume_file.filename.replace(".pdf", "").replace("_", " ").title()
            analysis = analyze_resume_with_openai(resume_text, job_description, candidate_name)

            results.append({
                "name": candidate_name,
                "filename": resume_file.filename,
                "score": analysis.get("score", 0),
                "summary": analysis.get("summary", ""),
                "strengths": analysis.get("strengths", []),
                "gaps": analysis.get("gaps", []),
                "recommendation": analysis.get("recommendation", ""),
            })

        except Exception as e:
            results.append({
                "name": resume_file.filename,
                "error": str(e),
                "score": 0,
            })

    # Sort by score descending (best candidates first)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    return JSONResponse(content={"candidates": results})


# ─── Run directly with: python main.py ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)