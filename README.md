# 🤖 Autonomous Job Hunter Agent

An enterprise-grade, Multi-Agent AI system built with **LangGraph**, **LangChain**, and **Ollama**. This agent autonomously searches the web for jobs, uses a hybrid local/cloud AI architecture to evaluate your fit, and writes perfectly tailored resumes and cover letters.

## 🏗️ Architecture

This project implements a state-machine workflow using LangGraph:

1. **Scout Agent:** Uses DuckDuckGo search to scrape job boards (LinkedIn, Indeed) for roles matching specific criteria.
2. **Persistent Memory:** Uses local JSON storage to remember jobs it has already evaluated to prevent duplicate applications.
3. **Manager Agent (Local AI):** Uses **Ollama (Llama 3)** running locally to analyze the job description for $0 and route it based on complexity.
4. **Evaluator Agent:** Deeply analyzes the job description against your resume and outputs a 0-100 match score.
5. **Tailor Agent (Cloud AI):** If the score is >= 75%, uses **Google Gemini** to rewrite your resume and draft a custom cover letter. 
6. **Auto-Apply Agent:** Uses **Playwright** browser automation to navigate to job portals and simulate applications.

## ⚙️ Prerequisites

1. **Python 3.10+**
2. **Ollama:** Installed locally ([ollama.com](https://ollama.com/)) with the Llama 3 model (`ollama run llama3`).
3. **Gemini API Key:** Get a free API key from Google AI Studio.

## 🚀 Setup

1. **Clone the repository**
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
4. **Setup Environment Variables:**
   Create a `.env` file in the root directory and add your API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
5. **Add your Resume:**
   Create a file named `base_resume.md` in the root directory containing your standard resume in Markdown format.

## 💻 Usage

Run the agent graph:
```bash
python agent_graph.py
```

Check the terminal output. If a matching job is found, the tailored documents will be saved as `tailored_resume.md` and `tailored_cover_letter.md`. Proof of browser automation will be saved as `application_proof.png`.

## 🛡️ Fallback Logic
This project uses LangChain `.with_fallbacks()`. If the primary Cloud LLM hits a rate limit (e.g., HTTP 429), it will seamlessly swap to a lighter model (`gemini-flash-lite-latest`) to ensure the agent pipeline never crashes.
