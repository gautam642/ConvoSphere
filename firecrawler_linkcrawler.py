import os
import sys
import json
import requests
from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv()


API_URL = "https://api.firecrawl.dev/v1/scrape"


def main():
    api_key = os.getenv("FIRECRAWLER_API_KEY")
    if not api_key:
        print("Missing FIRECRAWLER_API_KEY in environment/.env")
        print("Add: FIRECRAWLER_API_KEY=your_key")
        sys.exit(1)

    url = " ".join(sys.argv[1:]).strip()
    if not url:
        try:
            url = input("Enter URL to scrape: ").strip()
        except EOFError:
            url = ""
    if not url:
        print("No URL provided.")
        sys.exit(1)

    # Use official Firecrawl SDK
    client = Firecrawl(api_key=api_key)
    try:
        data = client.scrape(
            url,
            formats= ['markdown', 'html'],
        ).model_dump_json()
        # help(client.scrape(url))
    except Exception as e:
        print("Firecrawl scrape failed:", type(e).__name__, e)
        sys.exit(1)

    # Print the entire JSON response, nicely formatted
    print(json.dumps(data, indent=2, ensure_ascii=False))
    # print(data)


if __name__ == "__main__":
    main()

