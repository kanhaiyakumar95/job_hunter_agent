from typing import TypedDict, Optional

class AgentState(TypedDict):
    # Job Info
    job_title: Optional[str]
    job_url: Optional[str]
    job_description: str
    
    # User Info
    user_profile: str
    
    # Router State
    complexity: Optional[str] # "Simple" or "Complex"
    
    # Evaluator State
    match_score: Optional[int]
    evaluation_reasoning: Optional[str]
    
    # Tailor State
    tailored_resume: Optional[str]
    tailored_cover_letter: Optional[str]
