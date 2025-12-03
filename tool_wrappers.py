import os
import sys
import json
import subprocess
import asyncio
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class ToolWrappers:
    """Wrapper functions for all OSINT tools"""
    
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
    
    async def run_numverify(self, phone: str) -> Dict[str, Any]:
        """Run numverify phone validation"""
        try:
            print(f"🔍 Running numverify for phone: {phone}")
            cmd = [sys.executable, os.path.join(self.base_path, "numverify_fetcher.py"), phone]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                data = json.loads(stdout.decode())
                print(f"✅ Numverify completed successfully")
                return {"success": True, "data": data}
            else:
                print(f"❌ Numverify failed: {stderr.decode()}")
                return {"success": False, "error": stderr.decode()}
        except Exception as e:
            print(f"❌ Numverify exception: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_twitter_get(self, username: str) -> Dict[str, Any]:
        """Get Twitter user info by username"""
        try:
            print(f"🐦 Running Twitter fetch for username: {username}")
            username = username.lstrip('@')  # Remove @ if present
            cmd = [sys.executable, os.path.join(self.base_path, "twitter_info_fetcher.py"), "get", username]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                data = json.loads(stdout.decode())
                print(f"✅ Twitter fetch completed successfully")
                return {"success": True, "data": data}
            else:
                print(f"❌ Twitter fetch failed: {stderr.decode()}")
                return {"success": False, "error": stderr.decode()}
        except Exception as e:
            print(f"❌ Twitter fetch exception: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_linkedin_fetch(self, linkedin_urls: List[str]) -> Dict[str, Any]:
        """Fetch LinkedIn profile info"""
        try:
            print(f"💼 Running LinkedIn fetch for {len(linkedin_urls)} URLs")
            
            # Import and use the LinkedIn fetcher
            from linkedin_info_fetcher import LinkedInProfileInfo
            
            api_token = os.getenv("BRIGHTDATA_API_TOKEN", "").strip()
            dataset_id = os.getenv("BRIGHTDATA_DATASET_ID", "").strip()
            if not api_token:
                return {"success": False, "error": "Missing BRIGHTDATA_API_TOKEN in environment/.env"}
            collector = LinkedInProfileInfo(api_token, dataset_id)
            
            profiles = [{"url": url} for url in linkedin_urls]
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, collector.collect_profile_info, profiles)
            
            if success:
                # Read the saved data
                with open("profiles_by_url.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"✅ LinkedIn fetch completed successfully")
                return {"success": True, "data": data}
            else:
                print(f"❌ LinkedIn fetch failed")
                return {"success": False, "error": "LinkedIn collection failed"}
        except Exception as e:
            print(f"❌ LinkedIn fetch exception: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_serpapi(self, query: str) -> Dict[str, Any]:
        """Run SerpAPI Google search"""
        try:
            print(f"🔍 Running SerpAPI search: {query}")
            cmd = [sys.executable, os.path.join(self.base_path, "serpapi_tester.py"), query]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                data = json.loads(stdout.decode())
                print(f"✅ SerpAPI completed successfully")
                return {"success": True, "data": data}
            else:
                print(f"❌ SerpAPI failed: {stderr.decode()}")
                return {"success": False, "error": stderr.decode()}
        except Exception as e:
            print(f"❌ SerpAPI exception: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_firecrawl(self, url: str) -> Dict[str, Any]:
        """Scrape URL with Firecrawl"""
        try:
            print(f"🔥 Running Firecrawl for URL: {url}")
            cmd = [sys.executable, os.path.join(self.base_path, "firecrawler_linkcrawler.py"), url]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                data = json.loads(stdout.decode())
                print(f"✅ Firecrawl completed successfully")
                return {"success": True, "data": data}
            else:
                print(f"❌ Firecrawl failed: {stderr.decode()}")
                return {"success": False, "error": stderr.decode()}
        except Exception as e:
            print(f"❌ Firecrawl exception: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def extract_links_from_text(self, text: str) -> List[str]:
        """Extract URLs from text using regex"""
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
