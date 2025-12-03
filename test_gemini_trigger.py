import asyncio
import os
from dotenv import load_dotenv
from gemini_client import GeminiClient
from db.database import get_mongo_client, connect_to_mongo

load_dotenv()

async def test_gemini():
    print("--- Testing Gemini Client ---")
    try:
        client = GeminiClient()
        print("Client initialized.")
        
        response = await client.generate_content("Hello, are you working?")
        print(f"Gemini Response: {response}")
        
    except Exception as e:
        print(f"Gemini Client Error: {e}")

async def test_gemini_task_logic():
    print("\n--- Testing Gemini Task Logic (Mock) ---")
    # This simulates what run_gemini_call does
    try:
        client = GeminiClient()
        
        # Mock payload
        payload = {
            "session_id": "test_session",
            "task": "Test Task",
            "short_context": [{"role": "user", "content": "hi"}],
            "customer": {"name": "Test"},
            "local_llm_analysis": {"meta": {"timestamp": "now"}}
        }
        
        import json
        prompt = f"Analyze: {json.dumps(payload, indent=2)}"
        
        print("Sending prompt to Gemini...")
        response = await client.generate_content(prompt)
        print(f"Task Response: {response[:100]}...")
        
    except Exception as e:
        print(f"Task Logic Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
    asyncio.run(test_gemini_task_logic())
