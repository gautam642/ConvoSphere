import os
import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

import ollama

class OllamaGenerativeModel:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = ollama.AsyncClient(host='http://localhost:11434')

    async def generate(self, prompt: str) -> str:
        response = await self.client.chat(model=self.model_name, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']

llm_model_client = OllamaGenerativeModel(model_name="phi3:3.8b")


class LocalLLMService:
    async def analyze(self, session_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the current session context and returns a tactical analysis using the Elite Sales Strategist persona.
        """
        # Extract data from the payload
        short_context = session_payload.get("short_context", [])
        customer_info = session_payload.get("customer", {})
        osint_info = session_payload.get("osint", {})
        goal = session_payload.get("goal", "achieve a positive outcome")
        rag_context = session_payload.get("rag_context", "No specific RAG context available.") # Placeholder
        
        # Construct the detailed prompt
        # Construct the tactical prompt
        prompt = f"""
# ROLE AND OBJECTIVE
You are a Tactical Analyst for a sales conversation. Your job is to monitor the chat stream and provide instantaneous, lightweight analysis.

# INPUT CONTEXT
1. **Sales Goal**: {goal}
2. **Chat History**: {json.dumps(short_context, indent=2)}

# ANALYSIS INSTRUCTIONS
Analyze the latest interaction and the overall conversation flow.

# OUTPUT FORMAT
You must output **ONLY** a valid JSON object matching the schema below. Do not include markdown formatting or explanations outside the JSON.

```json
{{
  "global_summary": "Updated abstract of full conversation.",
  "latest_interaction_summary": "Specific summary of the last exchange.",
  "current_sentiment": "Client's current emotional state (e.g., Skeptical, Curious, Annoyed).",
  "conversation_state_tag": "One of: [Initializing, Rapport_Building, Needs_Discovery, Solution_Pitching, Objection_Handling, Closing, Stall, Dead]"
}}
```
"""
        
        try:
            # Add timeout for LLM generation (e.g., 30 seconds)
            try:
                raw_llm_output = await asyncio.wait_for(llm_model_client.generate(prompt), timeout=30.0)
            except asyncio.TimeoutError:
                print("--- Local LLM timed out. Using mock response. ---")
                # Mock response for fallback/testing
                raw_llm_output = """
```json
{
  "global_summary": "Conversation started, user inquiring about pricing.",
  "latest_interaction_summary": "User asked for enterprise pricing.",
  "current_sentiment": "Curious",
  "conversation_state_tag": "Needs_Discovery"
}
```
"""

            # Clean the output to extract only the JSON
            if "```json" in raw_llm_output:
                json_part = raw_llm_output.split("```json")[1].split("```")[0]
            elif "```" in raw_llm_output:
                json_part = raw_llm_output.split("```")[1].split("```")[0]
            else:
                json_part = raw_llm_output
            
            # Parse the JSON and return it
            analysis_json = json.loads(json_part)
            analysis_json["last_analysis_at"] = datetime.utcnow()
            
            # Update timestamp to current
            if "meta" in analysis_json:
                analysis_json["meta"]["timestamp"] = datetime.utcnow().isoformat()
                
            return analysis_json

        except json.JSONDecodeError as e:
            print(f"--- Local LLM analysis failed: Could not decode JSON. Error: {e} ---")
            return {
                "last_analysis_at": datetime.utcnow(),
                "error": f"JSONDecodeError: {e}. Raw output: {raw_llm_output}"
            }
        except Exception as e:
            print(f"--- Local LLM analysis failed: {e} ---")
            return {
                "last_analysis_at": datetime.utcnow(),
                "error": str(e)
            }


    async def suggest_first_message(self, session_payload: Dict[str, Any]) -> str:
        """
        Suggests an initial outbound message based on the person's info.
        This is a placeholder implementation.
        """
        customer_info = session_payload.get("customer", {})
        osint_info = session_payload.get("osint", {})
        goal = session_payload.get("goal", "")
        customer_name = customer_info.get("name", "there")
        customer_context = customer_info.get("context", "")

        prompt = f"Suggest a compelling first message for {customer_name}, with the goal of '{goal}', given their context: '{customer_context}'.\n\nPerson Info:\n{json.dumps(customer_info, indent=2)}\n\nOSINT Insights:\n{json.dumps(osint_info, indent=2)}\n\nTask: suggest_first_message"

        suggestion_text = await llm_model_client.generate(prompt)
        
        return suggestion_text.replace("{name}", customer_name).replace("{context}", customer_context) # Simple templating

def get_llm_service() -> LocalLLMService:
    return LocalLLMService()