from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import uuid

# Helper to generate UUIDs
def generate_uuid() -> str:
    return str(uuid.uuid4())
class Customer(BaseModel):
  name: str
  phone: str
  context: str
  goal: str
  telegram_user_id: Optional[int] = None
class OSINT(BaseModel):
    numverify: Optional[Dict[str, Any]] = None
    linkedin: Optional[Dict[str, Any]] = None
    github: Optional[Dict[str, Any]] = None
    serp: Optional[List[Dict[str, Any]]] = None
    firecrawl: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    status: Optional[str] = None  # "processing" | "completed" | "failed"
    data: Optional[Dict[str, Any]] = None  # Full OSINT enrichment data including final_summary
    error: Optional[str] = None
    completed_at: Optional[datetime] = None

class Message(BaseModel):
    message_id: str = Field(default_factory=generate_uuid)
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender: str # "agent" | "customer" | "system"
    channel: str # "telegram" | "streamlit"
    text: str
    telegram_user_id: Optional[int] = None # Added for Telegram message routing

class GeminiMeta(BaseModel):
    timestamp: str
    confidence_score: float

class GeminiAnalysisData(BaseModel):
    current_stage: str
    client_mode: str
    competitor_detected: bool
    red_flags: List[str]
    salesperson_critique: str

class GeminiTracker(BaseModel):
    trust_level: str
    pain_points_discovered: List[str]
    budget_clarity: str
    authority_status: str

class GeminiStrategy(BaseModel):
    suggested_next_message: str
    suggested_question: str
    personal_hook: str
    timing_suggestion: str

class GeminiObjections(BaseModel):
    predicted_next: str
    probability: float
    preemptive_tactic: str

class LocalLLMAnalysis(BaseModel):
    last_analysis_at: Optional[datetime] = None
    global_summary: Optional[str] = None
    latest_interaction_summary: Optional[str] = None
    current_sentiment: Optional[str] = None
    conversation_state_tag: Optional[str] = None
    error: Optional[str] = None

class GeminiAnalysis(BaseModel):
    last_call_at: Optional[datetime] = None
    meta: Optional[GeminiMeta] = None
    analysis: Optional[GeminiAnalysisData] = None
    tracker: Optional[GeminiTracker] = None
    strategy: Optional[GeminiStrategy] = None
    objections: Optional[GeminiObjections] = None
    payload_sent: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Alert(BaseModel):
    alert_id: str = Field(default_factory=generate_uuid)
    type: str # "high_intent" | "risk" | "info"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message: str

class Session(BaseModel):
    model_config = {"populate_by_name": True}
    session_id: str = Field(default_factory=generate_uuid, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner: str # sales_agent_id
    customer: Customer
    osint: OSINT = Field(default_factory=OSINT)
    messages: List[Message] = Field(default_factory=list)
    local_llm: LocalLLMAnalysis = Field(default_factory=LocalLLMAnalysis)
    gemini: GeminiAnalysis = Field(default_factory=GeminiAnalysis)
    alerts: List[Alert] = Field(default_factory=list)
    status: str = "initialized" # "initialized" | "active" | "closed"

# Request models
class CreateSessionRequest(BaseModel):
    name: str
    phone: str
    context: str
    goal: str
    owner_id: str

class NewMessageRequest(BaseModel):
    sender: str
    text: str
    channel: str
    telegram_user_id: Optional[int] = None

class SendMessageRequest(BaseModel):
    text: str
