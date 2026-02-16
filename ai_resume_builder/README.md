# 🤖 AI Resume Builder with Job Matching System

A production-ready, AI-powered resume builder that generates professional resumes, optimises them for ATS (Applicant Tracking Systems), calculates job-resume similarity scores using ML, and exports polished PDF files — all through a clean REST API.

---

## ✨ Features

| Feature                  | Description                                                                                    |
| ------------------------ | ---------------------------------------------------------------------------------------------- |
| **AI Resume Generation** | Creates professional summaries, skills sections & experience bullet points using Google Gemini |
| **ATS Optimisation**     | Restructures content for maximum Applicant Tracking System compatibility                       |
| **Job Matching**         | TF-IDF + cosine similarity scoring between resume & job description                            |
| **PDF Export**           | Generates clean, ATS-friendly PDF resumes via ReportLab                                        |
| **Keyword Analysis**     | Identifies matching & missing keywords for targeted improvements                               |
| **Recommendations**      | AI-generated suggestions to improve resume–job fit                                             |
| **REST API**             | Full FastAPI backend with Swagger documentation                                                |

---

## 🏗️ Tech Stack

- **Backend:** FastAPI 0.104
- **AI Engine:** Google Gemini 1.5 Flash (via `google-generativeai`)
- **ML / NLP:** scikit-learn (TF-IDF, cosine similarity)
- **PDF Generation:** ReportLab Platypus
- **Validation:** Pydantic v2
- **Templating:** Jinja2

---

## 📁 Project Structure

```
ai_resume_builder/
│
├── app/
│   ├── __init__.py              # Package init
│   ├── main.py                  # FastAPI application & endpoints
│   ├── agent.py                 # Gemini AI agent logic
│   ├── resume_generator.py      # PDF generation module
│   ├── job_matcher.py           # ML-based job matching
│   └── prompts.py               # Prompt templates
│
├── templates/
│   └── resume_template.html     # HTML resume template
│
├── static/                      # Static assets (future use)
├── output/                      # Generated PDF files
├── tests/
│   └── test_app.py              # Unit & integration tests
│
├── requirements.txt
├── .env                         # API keys (not committed)
├── .gitignore
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10+
- A Google Gemini API key ([get one free](https://aistudio.google.com/))

### 1. Clone the Repository

```bash
git clone https://github.com/Kris-gadara/AI-Resume-Builder.git
cd AI-Resume-Builder/ai_resume_builder
```

### 2. Create & Activate Virtual Environment

```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS / Linux)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Edit the `.env` file and replace the placeholder with your actual key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key
```

#### How to Get a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **"Get API key"** in the sidebar
4. Click **"Create API key"** → select or create a Google Cloud project
5. Copy the key into your `.env` file

### 5. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open API Documentation

Navigate to **http://localhost:8000/docs** for interactive Swagger UI.

---

## 📡 API Endpoints

### General

| Method | Endpoint  | Description                    |
| ------ | --------- | ------------------------------ |
| `GET`  | `/`       | API info & available endpoints |
| `GET`  | `/health` | Health check                   |

### Resume

| Method | Endpoint                   | Description                                            |
| ------ | -------------------------- | ------------------------------------------------------ |
| `POST` | `/api/generate-resume`     | Full AI pipeline → summary + skills + experience + PDF |
| `POST` | `/api/generate-pdf`        | Generate PDF from pre-built resume data                |
| `GET`  | `/api/download/{filename}` | Download a generated PDF                               |

### Job Matching

| Method | Endpoint                | Description                                 |
| ------ | ----------------------- | ------------------------------------------- |
| `POST` | `/api/analyze-match`    | Resume ↔ job description similarity score   |
| `POST` | `/api/extract-keywords` | Extract ATS keywords from a job description |

---

## 📋 Example API Calls

### Generate a Full Resume

```bash
curl -X POST http://localhost:8000/api/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "+1-555-123-4567",
    "skills": "Python, FastAPI, Machine Learning, SQL, Docker, AWS",
    "experience": "Software Engineer at Tech Corp for 3 years. Built REST APIs and ML pipelines. Led team of 4 developers.",
    "education": "B.S. Computer Science, MIT, 2020",
    "target_role": "Senior Python Developer",
    "job_description": "Looking for a Python developer with FastAPI experience, ML skills, and cloud deployment knowledge."
  }'
```

### Analyse Job Match

```bash
curl -X POST http://localhost:8000/api/analyze-match \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Experienced Python developer with FastAPI and ML expertise...",
    "job_description": "Senior Python developer needed with REST API and machine learning experience..."
  }'
```

### Generate PDF Only

```python
import requests

response = requests.post("http://localhost:8000/api/generate-pdf", json={
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+1-555-987-6543",
    "summary": "Results-driven engineer with 5+ years in Python...",
    "skills": "Python, Django, PostgreSQL, Docker",
    "experience": "Senior Developer at StartupX | 2019-2024\n• Built scalable APIs...",
    "education": "M.S. Computer Science, Stanford, 2019"
})
print(response.json())
```

---

## 🏛️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Client     │────▶│   FastAPI     │────▶│   Gemini AI      │
│  (REST API)  │     │   main.py     │     │   agent.py       │
└──────────────┘     └──────┬───────┘     └──────────────────┘
                           │
                    ┌──────┴───────┐
                    │              │
              ┌─────▼─────┐ ┌─────▼──────┐
              │ Job Matcher│ │ PDF Engine │
              │ (TF-IDF)  │ │ (ReportLab)│
              └───────────┘ └────────────┘
```

1. **Client** sends user data via REST endpoints.
2. **FastAPI** orchestrates the pipeline.
3. **Gemini AI** generates/optimises resume content.
4. **Job Matcher** computes TF-IDF cosine similarity.
5. **PDF Engine** exports a professional, ATS-friendly document.

---

## 🧪 Running Tests

```bash
# From the ai_resume_builder directory
pytest tests/ -v
```

---

## 🔮 Roadmap

### Phase 2

- [ ] Multi-agent system for specialised resume sections
- [ ] Multiple PDF templates (modern, classic, minimal)
- [ ] Cover letter generator
- [ ] LinkedIn profile optimisation

### Phase 3 — Production

- [ ] JWT authentication
- [ ] Database integration (PostgreSQL)
- [ ] Resume upload & parsing (PDF / DOCX)
- [ ] React frontend
- [ ] Docker deployment
- [ ] Rate limiting & caching
- [ ] Analytics dashboard

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Google Gemini API](https://ai.google.dev/) for AI content generation
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [scikit-learn](https://scikit-learn.org/) for ML-based text analysis
