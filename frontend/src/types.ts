// These types are based on the Pydantic models in the backend's schemas.py

export interface Customer {
  name: string;
  phone: string;
  context: string;
  goal: string;
}

export interface OSINT {
  numverify?: Record<string, any>;
  linkedin?: Record<string, any>;
  github?: Record<string, any>;
  serp?: Record<string, any>[];
  firecrawl?: Record<string, any>;
  confidence?: number;
  status?: 'processing' | 'completed' | 'failed';
  data?: Record<string, any>;  // Contains final_summary with person_profile, sales_intelligence, etc.
  error?: string;
  completed_at?: string;
}

export interface Message {
  message_id: string;
  session_id: string;
  timestamp: string; // ISO8601 string
  sender: 'agent' | 'customer' | 'system';
  channel: 'telegram' | 'streamlit';
  text: string;
}

export interface LocalLLMAnalysis {
  last_analysis_at?: string; // ISO8601 string
  global_summary?: string;
  latest_interaction_summary?: string;
  current_sentiment?: string;
  conversation_state_tag?: string;
  error?: string;
}

export interface GeminiAnalysis {
  last_call_at?: string; // ISO8601 string
  payload_sent?: Record<string, any>;
  response?: Record<string, any>;
  query_type?: 'user_query' | 'strategic_review';
  user_query?: string;
  error?: string;
}

export interface Alert {
  alert_id: string;
  type: string;
  created_at: string; // ISO8601 string
  message: string;
}

export interface Session {
  session_id: string;
  created_at: string; // ISO8601 string
  updated_at: string; // ISO8601 string
  owner: string;
  customer: Customer;
  osint: OSINT;
  messages: Message[];
  local_llm: LocalLLMAnalysis;
  gemini: GeminiAnalysis;
  alerts: Alert[];
  status: string;
}

// Request models
export interface CreateSessionRequest {
  name: string;
  phone: string;
  context: string;
  goal: string;
  owner_id: string;
}

export interface SendMessageRequest {
  text: string;
}
