import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()
def main():
    api_key = os.getenv("NUMVERIFY_KEY")
    if not api_key:
        print("Missing NUMVERIFY_KEY in environment/.env")
        print("Add: NUMVERIFY_KEY=your_key")
        sys.exit(1)

    number = " ".join(sys.argv[1:]).strip()
    if not number:
        try:
            number = input("Enter phone number (with country code, e.g. +14158586273): ").strip()
        except EOFError:
            number = ""
    if not number:
        print("No phone number provided.")
        sys.exit(1)

    params = {
        "access_key": api_key,
        "number": number,
        # Optional parameters:
        # "country_code": "",
        # "format": 1,
    }

    try:
        # Numverify validate endpoint
        resp = requests.get("https://apilayer.net/api/validate", params=params, timeout=30)
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

    # Numverify returns { success: false, error: {...} } on errors
    if isinstance(data, dict) and data.get("success") is False and "error" in data:
        print(json.dumps(data["error"], indent=2, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

