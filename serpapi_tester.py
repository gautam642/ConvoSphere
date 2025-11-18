import os
import sys
import json
import requests
from dotenv import load_dotenv
load_dotenv()
def main():
    api_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")
    if not api_key:
        print("Missing SERPAPI_API_KEY environment variable.")
        print("Export your key, e.g.: export SERPAPI_API_KEY=your_key")
        sys.exit(1)

    query = " ".join(sys.argv[1:]).strip()
    if not query:
        try:
            query = input("Enter your search query: ").strip()
        except EOFError:
            query = ""
    if not query:
        print("No query provided.")
        sys.exit(1)

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": "10",
        "hl": "en",
    }

    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    except requests.RequestException as e:
        print("Request failed:", type(e).__name__, e)
        sys.exit(1)

    if resp.status_code != 200:
        print(f"HTTP {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print(resp.text)
        sys.exit(1)

    organic = data.get("organic_results")
    out = {"organic_results": organic if organic is not None else []}
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
