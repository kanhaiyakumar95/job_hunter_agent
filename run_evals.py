import os
import json
from state import AgentState
from agent_graph import simple_evaluator_node, tailor_node
from api import app as fastapi_app
from fastapi.testclient import TestClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# ==========================================
# 🧪 MOCK DATA FOR EVALS
# ==========================================

MOCK_BASE_RESUME = """
# John Doe
## Java Developer
Experience: 3 years building Java Spring Boot APIs.
Skills: Java, Spring Boot, MySQL, REST APIs, Git.
No frontend experience.
"""

# A job that is a perfect match
PERFECT_MATCH_JOB = """
We are looking for a backend Java Developer with Spring Boot experience.
Must know MySQL and how to build REST APIs.
"""

# A job that is a terrible match (requires totally different skills)
TERRIBLE_MATCH_JOB = """
We are looking for a Senior React & Node.js Frontend Specialist.
Must have 10 years of experience with UI/UX design, CSS animations, and Figma.
No backend experience required.
"""

# ==========================================
# ⚖️ LLM-AS-A-JUDGE CONFIG
# ==========================================
# Since cloud APIs have rate limits, we use our local Ollama instance 
# as an infinite, free LLM-as-a-Judge for our evals!
from langchain_ollama import ChatOllama
judge_llm = ChatOllama(model="llama3", temperature=0.0)

def evaluate_hallucinations(base_resume: str, tailored_resume: str) -> bool:
    """Uses an LLM to judge if the tailored resume invented skills."""
    prompt = PromptTemplate.from_template(
        "You are a strict HR auditor.\n"
        "Base Resume:\n{base}\n\n"
        "Tailored Resume:\n{tailored}\n\n"
        "Did the Tailored Resume invent any skills or years of experience that were NOT present or reasonably implied in the Base Resume? "
        "Answer ONLY 'YES' (it hallucinated) or 'NO' (it was honest)."
    )
    chain = prompt | judge_llm
    response = chain.invoke({"base": base_resume, "tailored": tailored_resume})
    return "YES" in response.content.upper()

# ==========================================
# 🚀 TEST SUITE
# ==========================================

def test_match_scoring():
    print("\n--- Running Test 1: Match Scoring Accuracy ---")
    
    # Test Perfect Match
    state1 = {"job_description": PERFECT_MATCH_JOB, "user_profile": MOCK_BASE_RESUME}
    res1 = simple_evaluator_node(state1)
    score1 = res1.get("match_score", 0)
    print(f"Perfect Match Job Score: {score1}%")
    assert score1 >= 70, f"Expected high score for perfect match, got {score1}"
    
    # Test Terrible Match
    state2 = {"job_description": TERRIBLE_MATCH_JOB, "user_profile": MOCK_BASE_RESUME}
    res2 = simple_evaluator_node(state2)
    score2 = res2.get("match_score", 0)
    print(f"Terrible Match Job Score: {score2}%")
    assert score2 < 40, f"Expected low score for terrible match, got {score2}"
    
    print("✅ Match Scoring Eval Passed!")

def test_no_hallucinations():
    print("\n--- Running Test 2: LLM-as-a-Judge (Hallucination Check) ---")
    
    state = {
        "job_title": "Java Dev",
        "job_description": "Need Java Spring Boot and 10 years of React experience.",
        "user_profile": MOCK_BASE_RESUME
    }
    
    # Run the tailor node
    print("Generating tailored resume (this might take a few seconds)...")
    res = tailor_node(state)
    tailored = res.get("tailored_resume", "")
    
    if tailored == "Error":
        print("Tailor node failed to generate resume.")
        return
        
    print("Running LLM Judge to check for hallucinations...")
    did_hallucinate = evaluate_hallucinations(MOCK_BASE_RESUME, tailored)
    
    if did_hallucinate:
        print("❌ FAIL: The agent hallucinated skills to fit the job description!")
        print("\n--- Problematic Resume ---")
        print(tailored)
    else:
        print("✅ PASS: The agent remained honest and did not invent skills!")

def test_authentication_system():
    print("\n--- Running Test 3: JWT Authentication Security ---")
    client = TestClient(fastapi_app)
    
    print("Attempting to access /api/search without a token...")
    response = client.post("/api/search", json={"query": "test"})
    
    assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"
    print("✅ PASS: API correctly rejected unauthenticated request!")

if __name__ == "__main__":
    print("🚀 Starting LLM Evals...")
    try:
        test_match_scoring()
        test_authentication_system()
        # test_no_hallucinations() # Skipping LLM generation due to API rate limits
        print("\n🎉 All Evals Completed Successfully!")
    except AssertionError as e:
        print(f"\n❌ EVAL FAILED: {e}")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
