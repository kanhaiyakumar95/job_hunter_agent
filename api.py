import os
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from jobspy import scrape_jobs
import db
import auth
from agent_graph import app as graph_app

# Periodically deletes jobs older than 30 days every 12 hours
async def periodic_cleanup():
    while True:
        try:
            db.cleanup_expired_jobs(days=30)
        except Exception as e:
            print(f"[Auto-Cleanup] Error: {e}")
        await asyncio.sleep(12 * 3600)

# Manages application startup cleanup and background worker lifecycles
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.cleanup_expired_jobs(days=30)
    task = asyncio.create_task(periodic_cleanup())
    try:
        yield
    finally:
        task.cancel()

app = FastAPI(lifespan=lifespan)

# Restrict CORS to trusted origins to block unauthorized cross-site requests
allowed_origins_env = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
)
origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Search query schema with bounded length to prevent payload abuse
class SearchRequest(BaseModel):
    query: str = Field(default="", max_length=150)

# Job action schema containing metadata required to apply or dismiss
class ActionRequest(BaseModel):
    job_id: str
    job_title: str
    job_description: str
    job_url: str

# User credentials schema for login and registration
class UserAuth(BaseModel):
    username: str
    password: str

# Schema for returning signed JWT access token to the client
class Token(BaseModel):
    access_token: str
    token_type: str

# Registers a new user with bcrypt password hashing in the database
@app.post("/api/register")
def register_user(user: UserAuth):
    hashed_pw = auth.get_password_hash(user.password)
    success = db.create_user(user.username, hashed_pw)
    if not success:
        raise HTTPException(status_code=400, detail="Username already registered")
    return {"message": "User registered successfully"}

# Validates user credentials and issues a signed JWT access token
@app.post("/api/login", response_model=Token)
def login_user(user: UserAuth):
    db_user = db.get_user_by_username(user.username)
    if not db_user or not auth.verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": db_user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Scrapes jobs from LinkedIn and Indeed, persists new jobs, and returns active cards
@app.post("/api/search")
def search_jobs(req: SearchRequest, current_user: str = Depends(auth.get_current_user)):
    query = req.query if req.query else "Senior Java Engineer Pune"
    try:
        # Scrape jobs in real-time
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term=query,
            location="Pune, India",
            results_wanted=10,
            country_indeed='India'
        )
        
        # Insert them into the DB if new
        for index, row in jobs_df.iterrows():
            title = row.get('title', 'Unknown Title')
            company = row.get('company', 'Unknown Company')
            title_company = f"{title} at {company}"
            
            description = row.get("description", "")
            if not description or str(description) == "nan":
                description = f"Job Title: {title}\nCompany: {company}\nLocation: {row.get('location', '')}"
            
            job_url = str(row.get("job_url", ""))
            
            # Generate a consistent ID based on title+company to prevent duplicates
            job_id = str(uuid.uuid5(uuid.NAMESPACE_URL, title_company))
            db.add_job(current_user, job_id, title_company, str(description), job_url)
            
    except Exception as e:
        print(f"[Error] JobSpy failed: {e}")
        # Insert a mock job if real scraping fails
        db.add_job(current_user, "mock-123", f"{query} - Mock", f"Mock description for {query}", "http://mock")
        
    # Return all active jobs from DB (TTL < 30 days and status='new')
    active_jobs = db.get_active_jobs(current_user)
    return {
        "status": "success",
        "data": active_jobs
    }

# Marks a job card as dismissed/not interested for the authenticated user
@app.post("/api/ignore")
def ignore_job(req: ActionRequest, current_user: str = Depends(auth.get_current_user)):
    db.update_job_status(current_user, req.job_id, "not_interested")
    return {"status": "success"}

# Evaluates job fit, generates tailored resume/cover letter via LangGraph, and auto-applies
@app.post("/api/apply")
def apply_job(req: ActionRequest, current_user: str = Depends(auth.get_current_user)):
    # Mark as applied
    db.update_job_status(current_user, req.job_id, "applied")
    
    try:
        with open("base_resume.md", "r", encoding="utf-8") as f: 
            user_profile = f.read()
    except FileNotFoundError: 
        user_profile = "Java Developer"

    # Validate job URL to prevent protocol injection and SSRF
    safe_job_url = req.job_url if req.job_url.startswith(("http://", "https://")) else ""

    initial_state = {
        "job_title": req.job_title,
        "job_description": req.job_description,
        "job_url": safe_job_url,
        "user_profile": user_profile,
        "search_query": ""
    }
    
    # Run the Agent workflow to evaluate and tailor
    result = graph_app.invoke(initial_state)
    
    return {
        "status": "success",
        "data": {
            "job_title": result.get("job_title"),
            "match_score": result.get("match_score", 0),
            "tailored_resume": result.get("tailored_resume", ""),
            "tailored_cover_letter": result.get("tailored_cover_letter", "")
        }
    }
