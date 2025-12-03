import asyncio
import json
from services.local_llm_service import get_llm_service
from dotenv import load_dotenv

load_dotenv()

async def test_llm():
    service = get_llm_service()
    payload = {
        "short_context": [{"sender": "customer", "text": "Hi, I want to buy."}],
        "customer": {"name": "Test User", "goal": "Sell stuff"},
        "osint": {"job": "Engineer"},
        "goal": "Close the deal"
    }
    
    print("Calling analyze...")
    try:
        result = await service.analyze(payload)
        print("Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
