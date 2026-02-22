# 📄 Resume Screener

An AI-powered web app that ranks job candidates by analyzing their resumes against a job description using the OpenAI API.

**Built with:** FastAPI · OpenAI GPT-4o-mini · PyPDF2 · Vanilla JS

---

## ✨ Features

- Upload multiple PDF resumes via drag & drop
- Paste any job description
- AI scores each candidate 0–100 with strengths, gaps, and a hiring recommendation
- Results ranked automatically — best match first
- Clean, portfolio-ready UI

---
## Screenshots

![Form](assets/form.png)
![Results](assets/results.png)
![Detail](assets/details.png)
---
## 🚀 Setup (5 minutes)

### 1. Clone / download the project
```
resume-screener/
  main.py           ← FastAPI backend
  index.html        ← Frontend (served by FastAPI)
  requirements.txt  ← Python dependencies
  README.md
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your OpenAI API key
```bash
# Mac/Linux
export OPENAI_API_KEY="sk-..."

# Windows (Command Prompt)
set OPENAI_API_KEY=sk-...

# Or create a .env file and load it — see note below
```

> 💡 **Tip for beginners:** Add `from dotenv import load_dotenv; load_dotenv()` at the top of `main.py` and put your key in a `.env` file. Install with `pip install python-dotenv`.

### 5. Run the app
```bash
python main.py
```

Open your browser at **http://localhost:8000**

---

## 🧠 How it works (Learning guide)

```
User uploads PDFs + types JD
         │
         ▼
FastAPI /screen endpoint (POST)
         │
         ├─ PyPDF2 extracts text from each PDF
         │
         ├─ OpenAI GPT-4o-mini receives:
         │    - Job Description
         │    - Resume text (truncated to 4000 chars)
         │    - Structured JSON prompt
         │
         └─ Returns: score, summary, strengths, gaps, recommendation
                  │
                  ▼
            Frontend sorts + displays ranked cards
```

### Key concepts to study in the code

| File | What to learn |
|------|---------------|
| `main.py` lines 1–20 | FastAPI app setup, CORS middleware |
| `main.py` line 35–55 | Reading uploaded files with `UploadFile`, using `tempfile` |
| `main.py` line 57–95 | Prompt engineering — how to get structured JSON from an LLM |
| `main.py` line 98–145 | Handling multiple file uploads, error handling per file |
| `index.html` JS | `FormData` API for file uploads, `fetch` for async POST requests |
| `index.html` HTML/CSS | CSS custom properties, animations, responsive layout |

---

## 💡 Ideas to extend this project

- [ ] **Export to CSV** — add a download button for the ranked list
- [ ] **Keyword highlighting** — show which JD keywords were found/missing
- [ ] **Multiple JDs** — compare one resume against several roles
- [ ] **Auth + history** — add login and store past screenings in SQLite
- [ ] **Streaming** — use OpenAI streaming to show results as they come in
- [ ] **Batch mode** — process 50+ resumes with async concurrency (`asyncio.gather`)

---

## ⚠️ Notes

- **PDF text extraction** only works on text-based PDFs, not scanned images. For scanned resumes, you'd need OCR (e.g. `pytesseract`).
- **Cost:** GPT-4o-mini is very cheap (~$0.0001 per resume analysis). Screening 100 resumes costs roughly $0.01.
- **Privacy:** Resumes are processed in memory only — nothing is saved to disk or a database.
