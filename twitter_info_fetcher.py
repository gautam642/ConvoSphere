import os
import sys
import json
from dotenv import load_dotenv
import tweepy


load_dotenv()



def get_bearer() -> str:
    token = os.getenv("X_API_KEY") or os.getenv("TWITTER_BEARER_TOKEN") or ""
    token = token.strip()
    if token.startswith(("'", '"')) and token.endswith(("'", '"')):
        token = token[1:-1]
    return token


def get_user_by_username(client: tweepy.Client, username: str):
    return client.get_user(
        username=username,
        user_fields=[
            "id",
            "name",
            "username",
            "created_at",
            "description",
            "entities",
            "location",
            "pinned_tweet_id",
            "profile_image_url",
            "protected",
            "public_metrics",
            "url",
            "verified",
            "withheld",
        ],
    )


def get_oauth1_creds():
    ck = (os.getenv("X_CONSUMER_KEY") or os.getenv("TWITTER_CONSUMER_KEY") or "").strip()
    cs = (os.getenv("X_CONSUMER_SECRET") or os.getenv("TWITTER_CONSUMER_SECRET") or "").strip()
    at = (os.getenv("X_ACCESS_TOKEN") or os.getenv("TWITTER_ACCESS_TOKEN") or "").strip()
    ats = (os.getenv("X_ACCESS_TOKEN_SECRET") or os.getenv("TWITTER_ACCESS_TOKEN_SECRET") or "").strip()
    return ck, cs, at, ats


def get_v1_api() -> tweepy.API:
    ck, cs, at, ats = get_oauth1_creds()
    if not (ck and cs and at and ats):
        raise tweepy.TweepyException(
            "Missing OAuth1 credentials: set X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET"
        )
    auth = tweepy.OAuth1UserHandler(ck, cs, at, ats)
    return tweepy.API(auth, wait_on_rate_limit=True)


def get_timeline(client: tweepy.Client, name: str, max_results: int = 20):
    api = get_v1_api()
    count = max(1, min(int(max_results), 20))
    return api.user_timeline(screen_name=name)


def response_to_dict(resp) -> dict:
    out = {}
    if hasattr(resp, "data") and resp.data is not None:
        if isinstance(resp.data, list):
            out["data"] = [d.data if hasattr(d, "data") else dict(d) for d in resp.data]
        else:
            out["data"] = resp.data.data if hasattr(resp.data, "data") else dict(resp.data)
    elif isinstance(resp, list):
        out["data"] = [getattr(d, "_json", getattr(d, "__dict__", {})) for d in resp]
    if hasattr(resp, "includes") and resp.includes is not None:
        out["includes"] = resp.includes
    if hasattr(resp, "meta") and resp.meta is not None:
        out["meta"] = resp.meta
    return out


def main():
    bearer = get_bearer()
    if not bearer:
        print("Missing X_API_KEY/TWITTER_BEARER_TOKEN in environment/.env")
        print("Add: X_API_KEY=your_bearer_token")
        sys.exit(1)
    client = tweepy.Client(bearer_token=bearer, wait_on_rate_limit=True)

    # CLI usage:
    #   python twitter_info_fetcher.py get <username>
    #   python twitter_info_fetcher.py search <query>
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage:")
        print("  python3 twitter_info_fetcher.py get <username>")
        print("  python3 twitter_info_fetcher.py timeline <name>")
        # Interactive fallback
        try:
            mode = input("Mode (get/timeline): ").strip().lower()
        except EOFError:
            mode = ""
        if mode not in ("get", "timeline"):
            sys.exit(1)
        try:
            value = input("Enter username or query: ").strip()
        except EOFError:
            value = ""
    else:
        mode = args[0].lower()
        value = " ".join(args[1:]).strip()

    if mode == "get":
        if not value:
            print("Username is required for 'get'.")
            sys.exit(1)
        try:
            resp = get_user_by_username(client, value.lstrip("@"))
        except tweepy.TweepyException as e:
            print("Tweepy error:", type(e).__name__, e)
            sys.exit(1)
    elif mode == "timeline":
        if not value:
            print("Query is required for 'timeline'.")
            sys.exit(1)
        try:
            resp = get_timeline(client, value)
        except tweepy.TweepyException as e:
            print("Tweepy error:", type(e).__name__, e)
            sys.exit(1)
    else:
        print("Unknown mode. Use 'get' or 'timeline'.")
        sys.exit(1)

    data = response_to_dict(resp)
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

