# 🤖 Autonomous Job Hunter Agent (Tinder for Jobs)

An enterprise-grade, Multi-Agent AI system built with **LangGraph**, **FastAPI**, **React**, and **Ollama**. This agent autonomously scrapes job boards, presents them in an interactive "Tinder-style" UI, and upon clicking "Auto-Apply", evaluates your fit and writes perfectly tailored resumes and cover letters.

## 🏗️ Architecture

This project is separated into a modular frontend and backend, using a decoupled scraping and evaluation pipeline:

### Backend (FastAPI + SQLite + LangGraph)
1. **API Router (`api.py`)**: Handles frontend requests. Protects endpoints using OAuth2 Password Bearer authentication, validates request payloads, restricts CORS to trusted origins, and runs an automated 30-day TTL cleanup background worker.
2. **Security (`auth.py`)**: Implements stateless JWT (JSON Web Token) authentication with bcrypt password hashing and startup validation warnings for secrets.
3. **JobSpy Scraper**: Real-time web scraper replacing standard search engines for scraping LinkedIn and Indeed directly.
4. **SQLite Database (`db.py`)**: Stores user accounts (hashed passwords) and scraped jobs. Enforces automatic 30-day TTL cleanup on application boot and periodically.
5. **LangGraph Agent (`agent_graph.py`)**:
   - **Manager Node:** Uses **Ollama (Llama 3)** running locally to analyze the job description and route it based on complexity.
   - **Evaluator Node (NLP):** Uses a lightning-fast, $0.00 mathematical NLP algorithm (Jaccard Similarity) to instantly calculate a keyword overlap score (0-100) between your resume and the job description. Throws out terrible matches instantly.
   - **Tailor Node:** If the math score is high enough, uses **Google Gemini** with structured prompt injection delimiters to rewrite your resume and draft a custom cover letter. 
   - **Auto-Apply Node:** Uses **Playwright** browser automation with scheme validation to safely navigate to job portals and capture proof of application.

### Frontend (React + Vite + Framer Motion)
- **`App.jsx`**: The main interface for searching and viewing jobs, featuring `DOMPurify` sanitization for rendered resumes and strict URL protocol validation.
- **`<JobCard />` Component**: A beautifully animated, framer-motion driven card. Users can click `Ignore` (status: `not_interested`) or `Auto-Apply` (status: `applied`).

## ⚙️ Prerequisites

1. **Python 3.10+**
2. **Node.js (for React frontend)**
3. **Ollama:** Installed locally ([ollama.com](https://ollama.com/)) with the Llama 3 model (`ollama run llama3`).
4. **Gemini API Key:** Get a free API key from Google AI Studio.

## 🚀 Setup

1. **Clone the repository**
2. **Backend Setup:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **Frontend Setup:**
   ```bash
   cd react-frontend
   npm install
   ```
4. **Environment Variables:**
   Create a `.env` file in the root directory and add your API key and JWT secret:
   ```env
   GEMINI_API_KEY=your_api_key_here
   JWT_SECRET=super_secret_local_key_123
   ```
5. **Add your Resume:**
   Create a file named `base_resume.md` in the root directory containing your standard resume in Markdown format.

## 💻 Usage

Start the backend server (Terminal 1):
```bash
# Windows
$env:PYTHONIOENCODING="utf-8"
venv\Scripts\uvicorn api:app --host 0.0.0.0 --port 8080
```

Start the React frontend (Terminal 2):
```bash
cd react-frontend
npm run dev
```

Navigate to `http://localhost:5173` in your browser. Enter a search query and swipe through your job matches!

## 🛡️ Fallback Logic
This project uses LangChain `.with_fallbacks()`. If the primary Cloud LLM hits a rate limit (e.g., HTTP 429), it will seamlessly swap to a lighter model (`gemini-flash-lite-latest`) to ensure the agent pipeline never crashes.
