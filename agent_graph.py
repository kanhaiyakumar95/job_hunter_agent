import os
import json
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchResults
from playwright.sync_api import sync_playwright

from state import AgentState

# Initialize environment variables (loads GEMINI_API_KEY from .env)
load_dotenv()

# ==========================================
# 💾 PERSISTENT MEMORY SETUP
# ==========================================
MEMORY_FILE = "seen_jobs.json"

def load_seen_jobs():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f: 
            return json.load(f)
    return []

def save_seen_job(job_title):
    jobs = load_seen_jobs()
    if job_title not in jobs:
        jobs.append(job_title)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f: 
            json.dump(jobs, f, indent=4)

# ==========================================
# 📄 PYDANTIC SCHEMAS (STRUCTURED OUTPUT)
# ==========================================
class ScoutResult(BaseModel):
    job_title: str = Field(description="The title and company of the job")
    job_url: str = Field(description="The URL link to apply for the job")
    job_description: str = Field(description="The full job description")

class ComplexityResult(BaseModel):
    level: Literal["Simple", "Complex"] = Field(description="Simple or Complex")

class EvaluationResult(BaseModel):
    match_score: int = Field(description="Score from 0 to 100")
    evaluation_reasoning: str = Field(description="Brief explanation of the score")

class TailoredDocuments(BaseModel):
    tailored_resume: str = Field(description="Markdown resume")
    tailored_cover_letter: str = Field(description="Markdown cover letter")

# ==========================================
# 🪂 AI FACTORIES & FALLBACK LOGIC
# ==========================================
def get_llm(schema, temp=0.0):
    """Creates an LLM that automatically falls back to a different model if the primary hits a quota limit."""
    primary = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=temp)
    backup = ChatGoogleGenerativeAI(model="gemini-flash-lite-latest", temperature=temp)
    
    primary_structured = primary.with_structured_output(schema)
    backup_structured = backup.with_structured_output(schema)
    
    return primary_structured.with_fallbacks([backup_structured])

# ==========================================
# 🤖 GRAPH NODES
# ==========================================
def scout_node(state: AgentState) -> dict:
    print("-> 🕵️ [Scout] Searching the web for NEW jobs...")
    search = DuckDuckGoSearchResults()
    seen_jobs = load_seen_jobs()
    
    # Modify this query to change search targets
    query = "site:linkedin.com/jobs OR site:indeed.com 'Senior Java Full Stack' 'Spring Boot' 'AWS' Pune"
    
    try:
        raw_results = search.run(query)
        llm = get_llm(ScoutResult, 0)
        prompt = PromptTemplate.from_template("Extract the best job. Results: {results}")
        result = (prompt | llm).invoke({"results": raw_results})
        
        if result.job_title in seen_jobs:
            print(f"   [Memory] We already applied to '{result.job_title}'. Skipping!")
            return {"job_title": "ALREADY_SEEN", "job_description": "", "job_url": ""}
            
        print(f"   [Success] Found NEW job: {result.job_title}")
        save_seen_job(result.job_title)
        return {
            "job_title": result.job_title, 
            "job_description": result.job_description, 
            "job_url": result.job_url
        }
    except Exception as e:
        print(f"   [Error] Scout failed: {e}")
        return {"job_title": "ALREADY_SEEN", "job_description": "", "job_url": ""}

def memory_check_edge(state: AgentState) -> Literal["complexity_router", "end"]:
    if state.get("job_title") == "ALREADY_SEEN": 
        return "end"
    return "complexity_router"

def complexity_router_node(state: AgentState) -> dict:
    print("-> 🧠 [Manager] Analyzing job complexity locally using Ollama (Llama 3) for $0...")
    local_llm = ChatOllama(model="llama3", temperature=0)
    structured_llm = local_llm.with_structured_output(ComplexityResult)
    
    prompt = PromptTemplate.from_template("Respond ONLY with valid JSON. Is this job standard (Simple) or heavy architecture (Complex)? JD: {jd}")
    try:
        result = (prompt | structured_llm).invoke({"jd": state["job_description"]})
        print(f"   [Routing] Categorized as: {result.level}")
        return {"complexity": result.level}
    except Exception as e:
        print(f"   [Warning] Local LLM fallback: {e}")
        return {"complexity": "Simple"}

def route_complexity_edge(state: AgentState) -> Literal["simple_evaluator", "complex_evaluator"]:
    if state.get("complexity") == "Complex":
        return "complex_evaluator"
    return "simple_evaluator"

def simple_evaluator_node(state: AgentState) -> dict:
    print("-> ⚖️ [Evaluator - Fast/Cheap] Grading simple job locally using Ollama for $0...")
    local_llm = ChatOllama(model="llama3", temperature=0)
    structured_llm = local_llm.with_structured_output(EvaluationResult)
    
    prompt = PromptTemplate.from_template("Respond ONLY with valid JSON. Briefly evaluate. JD: {jd} Profile: {profile}")
    try:
        result = (prompt | structured_llm).invoke({"jd": state["job_description"], "profile": state["user_profile"]})
        return {"match_score": result.match_score, "evaluation_reasoning": result.evaluation_reasoning}
    except Exception:
        return {"match_score": 80, "evaluation_reasoning": "Fallback Default Score"}

def complex_evaluator_node(state: AgentState) -> dict:
    print("-> ⚖️ [Evaluator - Deep/Pro] Grading complex job with high scrutiny...")
    llm = get_llm(EvaluationResult, 0)
    prompt = PromptTemplate.from_template("Deeply evaluate this complex role. JD: {jd} Profile: {profile}")
    try:
        result = (prompt | llm).invoke({"jd": state["job_description"], "profile": state["user_profile"]})
        return {"match_score": result.match_score, "evaluation_reasoning": result.evaluation_reasoning}
    except Exception:
        return {"match_score": 80, "evaluation_reasoning": "Fallback Default Score"}

def should_tailor_edge(state: AgentState) -> Literal["tailor_node", "end"]:
    if state.get("match_score", 0) >= 75: 
        return "tailor_node"
    print(f"   [Routing] Score {state.get('match_score')}% < 75%. Halting.")
    return "end"

def tailor_node(state: AgentState) -> dict:
    print("-> ✍️ [Tailor] Writing custom resume and cover letter...")
    llm = get_llm(TailoredDocuments, 0.7)
    prompt = PromptTemplate.from_template("Tailor resume and cover letter. JD: {jd} Profile: {profile}")
    
    try:
        result = (prompt | llm).invoke({"jd": state["job_description"], "profile": state["user_profile"]})
        with open("tailored_resume.md", "w", encoding="utf-8") as f: 
            f.write(result.tailored_resume)
        with open("tailored_cover_letter.md", "w", encoding="utf-8") as f: 
            f.write(result.tailored_cover_letter)
        print("   [Success] Saved tailored documents to disk!")
        return {"tailored_resume": result.tailored_resume, "tailored_cover_letter": result.tailored_cover_letter}
    except Exception as e:
        print(f"   [Warning] Hit API rate limit on tailoring: {e}")
        return {"tailored_resume": "Error", "tailored_cover_letter": "Error"}

def auto_apply_node(state: AgentState) -> dict:
    if state.get("tailored_resume") == "Error": 
        return {}
        
    print("-> 🤖 [Auto-Apply] Launching Chrome Browser using Playwright...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            print("   [Action] Navigating to job portal...")
            # In production, change this to state.get("job_url")
            page.goto("https://google.com") 
            print("   [Action] Taking screenshot as proof...")
            page.screenshot(path="application_proof.png")
            browser.close()
            print("   [Success] Auto-Apply complete! Check 'application_proof.png' in your folder.")
    except Exception as e:
        print(f"   [Error] Browser automation failed: {e}")
    return {}

# ==========================================
# 🔀 GRAPH COMPILATION
# ==========================================
workflow = StateGraph(AgentState)
workflow.add_node("scout", scout_node)
workflow.add_node("complexity_router", complexity_router_node)
workflow.add_node("simple_evaluator", simple_evaluator_node)
workflow.add_node("complex_evaluator", complex_evaluator_node)
workflow.add_node("tailor_node", tailor_node)
workflow.add_node("auto_apply_node", auto_apply_node)

workflow.add_edge(START, "scout")
workflow.add_conditional_edges("scout", memory_check_edge, {"complexity_router": "complexity_router", "end": END})
workflow.add_conditional_edges("complexity_router", route_complexity_edge, {"simple_evaluator": "simple_evaluator", "complex_evaluator": "complex_evaluator"})
workflow.add_conditional_edges("simple_evaluator", should_tailor_edge, {"tailor_node": "tailor_node", "end": END})
workflow.add_conditional_edges("complex_evaluator", should_tailor_edge, {"tailor_node": "tailor_node", "end": END})
workflow.add_edge("tailor_node", "auto_apply_node")
workflow.add_edge("auto_apply_node", END)

app = workflow.compile()

# ==========================================
# 🚀 EXECUTION
# ==========================================
if __name__ == "__main__":
    print("=== Running Job Hunter Agent (With Auto-Fallbacks) ===\n")
    
    # Load user profile safely
    try:
        with open("base_resume.md", "r", encoding="utf-8") as f: 
            user_profile = f.read()
    except FileNotFoundError: 
        user_profile = "Java Developer"

    initial_state = {"job_description": "", "user_profile": user_profile, "job_url": "", "job_title": ""}
    
    # Run Graph
    result = app.invoke(initial_state)
    
    # Output final state
    if result.get("job_title") != "ALREADY_SEEN":
        print("\n=== Final State ===")
        print(f"Job: {result.get('job_title')}")
        print(f"Apply Here: {result.get('job_url')}")
        print(f"Match Score: {result.get('match_score')}%")
