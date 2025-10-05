from typing import List, Optional, Dict, Any
from pydantic import BaseModel

""""
This file serves to initialize the different models we plan to use for both state management in langgraph and for structured data extraction. 
"""

# This is the schema we feed into the LLM after it has scraped the info from the web already so it can populate these fields
class CompanyAnalysis(BaseModel):
    """Structured output for LLM company analysis focused on developer tools"""
    pricing_model: str  # Free, Freemium, Paid, Enterprise, Unknown
    is_open_source: Optional[bool] = None
    tech_stack: List[str] = []
    description: str = ""
    api_available: Optional[bool] = None
    language_support: List[str] = []
    integration_capabilities: List[str] = []


# This is our schema for how we want to store Company info for the companies we scrape and extract tools from
class CompanyInfo(BaseModel):
    name: str
    description: str
    website: str
    pricing_model: Optional[str] = None
    is_open_source: Optional[bool] = None
    tech_stack: List[str] = []
    competitors: List[str] = []
    # Developer-specific fields
    api_available: Optional[bool] = None
    language_support: List[str] = []
    integration_capabilities: List[str] = []
    developer_experience_rating: Optional[str] = None  # Poor, Good, Excellent


# This is like the AgentState Class for Langgraph usage
class ResearchState(BaseModel):
    query: str
    extracted_tools: List[str] = []    # Tools that are extracted from articles during research
    companies: List[CompanyInfo] = []   # All the companies that we extracted from our scraping procedure
    search_results: List[Dict[str, Any]] = []
    analysis: Optional[str] = None    
