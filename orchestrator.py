import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from tool_wrappers import ToolWrappers
from gemini_client import GeminiClient

class PersonOSINTOrchestrator:
    """Main orchestrator for person OSINT enrichment using Gemini API"""
    
    def __init__(self):
        self.tools = ToolWrappers()
        self.gemini = GeminiClient()
        self.person_info = {}  # Global person info storage
        
    def log_step(self, step: int, message: str):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] STEP {step}: {message}")
    
    async def enrich_person(self, phone: str, name: str, context_info: str) -> Dict[str, Any]:
        """
        Main orchestration flow following your specified steps:
        1. Numverify phone validation
        2. Gemini parsing of input info
        3. First wave enrichment (Twitter, LinkedIn, SerpAPI)
        4. Gemini link filtering
        5. Second wave enrichment (Firecrawl on filtered links)
        6. Link extraction and additional scraping
        6.5. Gemini parsing of all scraped content to extract relevant info
        7. Final Gemini summary with ground truth verification
        """
        
        # Initialize person_info with ground truth
        self.person_info = {
            "ground_truth": {
                "name": name,
                "phone": phone,
                "context_info": context_info,
                "timestamp": datetime.now().isoformat()
            },
            "enrichment_data": {},
            "tool_outputs": {},
            "processing_log": []
        }
        
        try:
            # STEP 1: Phone validation with numverify
            await self._step1_phone_validation(phone)
            
            # STEP 2: Gemini parsing of initial info
            await self._step2_gemini_parsing(name, phone, context_info)
            
            # STEP 3: First wave enrichment
            await self._step3_first_wave_enrichment()
            
            # STEP 4: Gemini link filtering from search results
            await self._step4_gemini_link_filtering()
            
            # STEP 5: Second wave enrichment on filtered links
            await self._step5_second_wave_enrichment()
            
            # STEP 6: Extract links from social media and scrape
            await self._step6_link_extraction_and_scraping()
            
            # STEP 6.5: Parse all scraped content with Gemini
            await self._step6_5_parse_scraped_content()
            
            # STEP 7-8: Final summary with ground truth verification
            final_summary = await self._step7_8_final_summary()
            
            self.person_info["final_summary"] = final_summary
            
            return self.person_info
            
        except Exception as e:
            self.log_step(0, f"❌ CRITICAL ERROR: {str(e)}")
            self.person_info["error"] = str(e)
            return self.person_info
    
    async def _step1_phone_validation(self, phone: str):
        """Step 1: Run phone through numverify to get country details"""
        self.log_step(1, f"Validating phone number: {phone}")
        
        numverify_result = await self.tools.run_numverify(phone)
        self.person_info["tool_outputs"]["numverify"] = numverify_result
        
        # Print raw output
        print(f"📄 RAW NUMVERIFY OUTPUT:")
        print(json.dumps(numverify_result, indent=2))
        print("-" * 50)
        
        if numverify_result["success"]:
            country_info = numverify_result["data"]
            self.person_info["enrichment_data"]["country"] = country_info.get("country_name", "Unknown")
            self.person_info["enrichment_data"]["country_code"] = country_info.get("country_code", "Unknown")
            self.person_info["enrichment_data"]["phone_valid"] = country_info.get("valid", False)
            self.log_step(1, f"✅ Phone validated - Country: {country_info.get('country_name', 'Unknown')}")
        else:
            self.log_step(1, f"❌ Phone validation failed: {numverify_result.get('error', 'Unknown error')}")
            self.person_info["enrichment_data"]["country"] = "Unknown"
            self.person_info["enrichment_data"]["phone_valid"] = False
    
    async def _step2_gemini_parsing(self, name: str, phone: str, context_info: str):
        """Step 2: Gemini parsing of person info and Google query generation"""
        self.log_step(2, "Parsing person info with Gemini API")
        
        country_info = self.person_info["tool_outputs"].get("numverify", {}).get("data", {})
        
        parsed_info = await self.gemini.parse_initial_info(name, phone, context_info, country_info)
        self.person_info["enrichment_data"]["parsed_info"] = parsed_info
        
        # Print raw output
        print(f"📄 RAW GEMINI PARSING OUTPUT:")
        print(json.dumps(parsed_info, indent=2))
        print("-" * 50)
        
        # Extract structured data
        self.person_info["enrichment_data"]["links_mentioned"] = parsed_info.get("links_mentioned", [])
        self.person_info["enrichment_data"]["usernames_mentioned"] = parsed_info.get("usernames_mentioned", {})
        self.person_info["enrichment_data"]["company_info"] = parsed_info.get("company_info", {})
        self.person_info["enrichment_data"]["google_search_query_to_get_linkedin_profile"] = parsed_info.get("google_search_query_to_get_linkedin_profile", f'"{name}" profile linkedin')
        self.person_info["enrichment_data"]["google_search_to_get_usernames_links_queries"] = parsed_info.get("google_search_to_get_usernames_links_queries", [f'"{name}" twitter', f'"{name}" github'])
        self.person_info["enrichment_data"]["google_search_query_to_get_company_profile"] = parsed_info.get("google_search_query_to_get_company_profile", f'"{name}" company profile')
        self.person_info["enrichment_data"]["google_search_generic_query"] = parsed_info.get("google_search_generic_query", f'"{name}" profile')
        
        self.log_step(2, f"✅ Parsed info - Found {len(parsed_info.get('links_mentioned', []))} links, {len(parsed_info.get('usernames_mentioned', {}))} usernames")
    
    async def _step3_first_wave_enrichment(self):
        """Step 3: First wave of tool calls based on parsed info"""
        self.log_step(3, "Starting first wave enrichment")
        
        tasks = []
        
        # Twitter enrichment if username found
        twitter_username = self.person_info["enrichment_data"]["usernames_mentioned"].get("twitter")
        if twitter_username:
            self.log_step(3, f"Found Twitter username: {twitter_username}")
            tasks.append(self._enrich_twitter(twitter_username))
        
        # LinkedIn enrichment if URL found
        linkedin_urls = [url for url in self.person_info["enrichment_data"]["links_mentioned"] 
                        if "linkedin.com" in url]
        if linkedin_urls:
            self.log_step(3, f"Found {len(linkedin_urls)} LinkedIn URLs")
            tasks.append(self._enrich_linkedin(linkedin_urls))
        
        # Multiple Google searches with generated queries
        search_queries = []
        
        # LinkedIn profile search
        linkedin_query = self.person_info["enrichment_data"]["google_search_query_to_get_linkedin_profile"]
        search_queries.append(("linkedin_search", linkedin_query))
        
        # Username/platform searches
        username_queries = self.person_info["enrichment_data"]["google_search_to_get_usernames_links_queries"]
        for i, query in enumerate(username_queries):
            search_queries.append((f"username_search_{i}", query))
        
        # Company profile search
        company_query = self.person_info["enrichment_data"]["google_search_query_to_get_company_profile"]
        search_queries.append(("company_search", company_query))
        
        # Generic search
        generic_query = self.person_info["enrichment_data"]["google_search_generic_query"]
        search_queries.append(("generic_search", generic_query))
        
        # Run all search queries
        for search_type, query in search_queries:
            self.log_step(3, f"Running {search_type}: {query}")
            tasks.append(self._enrich_serpapi_with_key(search_type, query))
        
        # Run all tasks concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.log_step(3, "✅ First wave enrichment completed")
    
    async def _step4_gemini_link_filtering(self):
        """Step 4: Use Gemini to filter and prioritize search results"""
        self.log_step(4, "Filtering search results with Gemini")
        
        # Collect all search results from different queries
        all_search_results = {}
        for key, result in self.person_info["tool_outputs"].items():
            if key.startswith(("linkedin_search", "username_search", "company_search", "generic_search")):
                all_search_results[key] = result
                
                # Print raw search results for each query
                print(f"📄 RAW SERPAPI OUTPUT ({key}):")
                print(json.dumps(result, indent=2))
                print("-" * 50)
        
        if all_search_results:
            # Combine all search results for filtering
            combined_results = {"combined_searches": all_search_results}
            
            filtered_links = await self.gemini.filter_search_links(
                self.person_info["enrichment_data"], 
                combined_results
            )
            
            # Limit to top 5 links for Firecrawl
            self.person_info["enrichment_data"]["priority_links"] = filtered_links[:5]
            
            # Print filtered links
            print(f"📄 GEMINI FILTERED LINKS (TOP 5):")
            print(json.dumps(self.person_info["enrichment_data"]["priority_links"], indent=2))
            print("-" * 50)
            
            self.log_step(4, f"✅ Filtered to {len(self.person_info['enrichment_data']['priority_links'])} priority links for Firecrawl")
        else:
            self.person_info["enrichment_data"]["priority_links"] = []
            self.log_step(4, "❌ No search results to filter")
    
    async def _step5_second_wave_enrichment(self):
        """Step 5: Second wave enrichment on filtered links"""
        self.log_step(5, "Starting second wave enrichment on priority links")
        
        priority_links = self.person_info["enrichment_data"].get("priority_links", [])
        tasks = []
        
        for link in priority_links:
            if "linkedin.com" in link and "linkedin" not in self.person_info["tool_outputs"]:
                # LinkedIn not done yet
                tasks.append(self._enrich_linkedin([link]))
            elif any(domain in link for domain in ["twitter.com", "x.com"]) and "twitter" not in self.person_info["tool_outputs"]:
                # Extract Twitter username and fetch
                username = self._extract_twitter_username(link)
                if username:
                    tasks.append(self._enrich_twitter(username))
            else:
                # Use Firecrawl for other links
                tasks.append(self._enrich_firecrawl(link))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.log_step(5, "✅ Second wave enrichment completed")
    
    async def _step6_link_extraction_and_scraping(self):
        """Step 6: Extract links from social media content and scrape them"""
        self.log_step(6, "Extracting additional links from social media content")
        
        # Extract links from Twitter bio/description
        twitter_data = self.person_info["tool_outputs"].get("twitter", {}).get("data", {})
        if twitter_data.get("success") and "data" in twitter_data:
            user_data = twitter_data["data"]
            description = user_data.get("description", "")
            
            # Extract URLs from Twitter bio
            extracted_links = self.tools.extract_links_from_text(description)
            
            if extracted_links:
                self.log_step(6, f"Found {len(extracted_links)} links in Twitter bio")
                
                # Scrape extracted links with Firecrawl
                tasks = [self._enrich_firecrawl(link) for link in extracted_links[:3]]  # Limit to 3 links
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
        
        self.log_step(6, "✅ Link extraction and scraping completed")
    
    async def _step6_5_parse_scraped_content(self):
        """Step 6.5: Parse all Firecrawl outputs with Gemini to extract relevant information"""
        self.log_step(6.5, "Parsing scraped content with Gemini")
        
        # Find all Firecrawl outputs
        firecrawl_outputs = {k: v for k, v in self.person_info["tool_outputs"].items() 
                           if k.startswith("firecrawl")}
        
        if not firecrawl_outputs:
            self.log_step(6.5, "No scraped content to parse")
            return
        
        # Initialize parsed content storage
        self.person_info["enrichment_data"]["parsed_scraped_content"] = {}
        
        # Parse each scraped content with Gemini
        parsing_tasks = []
        for key, scraped_data in firecrawl_outputs.items():
            if scraped_data.get("success"):
                parsing_tasks.append(self._parse_single_scraped_content(key, scraped_data))
        
        if parsing_tasks:
            parsed_results = await asyncio.gather(*parsing_tasks, return_exceptions=True)
            
            # Store successful parsing results
            for i, result in enumerate(parsed_results):
                if isinstance(result, dict) and not result.get("not_target_person", True):
                    key = list(firecrawl_outputs.keys())[i]
                    self.person_info["enrichment_data"]["parsed_scraped_content"][key] = result
                    
                    # Print raw parsed content
                    print(f"📄 RAW GEMINI PARSED CONTENT ({key}):")
                    print(json.dumps(result, indent=2))
                    print("-" * 50)
                    
                    relevance = result.get("relevance_score", 0.0)
                    self.log_step(6.5, f"✅ Parsed {key} - Relevance: {relevance:.2f}")
                else:
                    key = list(firecrawl_outputs.keys())[i] if i < len(firecrawl_outputs) else f"unknown_{i}"
                    self.log_step(6.5, f"❌ Skipped {key} - Not relevant or parsing failed")
        
        parsed_count = len(self.person_info["enrichment_data"]["parsed_scraped_content"])
        self.log_step(6.5, f"✅ Content parsing completed - {parsed_count} relevant sources found")
    
    async def _parse_single_scraped_content(self, key: str, scraped_data: Dict) -> Dict[str, Any]:
        """Parse a single scraped content item with Gemini"""
        return await self.gemini.parse_scraped_content(
            scraped_data,
            self.person_info["enrichment_data"],
            self.person_info["ground_truth"]
        )
    
    async def _step7_8_final_summary(self) -> Dict[str, Any]:
        """Steps 7-8: Generate final summary with ground truth verification"""
        self.log_step(7, "Generating final summary with ground truth verification")
        
        # Prepare all collected data for Gemini
        all_collected_data = {
            "tool_outputs": self.person_info["tool_outputs"],
            "enrichment_data": self.person_info["enrichment_data"]
        }
        
        final_summary = await self.gemini.verify_and_summarize(
            self.person_info["ground_truth"],
            all_collected_data
        )
        
        # Print raw final summary
        print(f"📄 RAW FINAL SUMMARY:")
        print(json.dumps(final_summary, indent=2))
        print("-" * 50)
        
        self.log_step(8, f"✅ Final summary completed - Status: {final_summary.get('verification_status', 'Unknown')}")
        
        return final_summary
    
    # Helper methods for individual tool enrichment
    async def _enrich_twitter(self, username: str):
        """Enrich with Twitter data"""
        result = await self.tools.run_twitter_get(username)
        self.person_info["tool_outputs"]["twitter"] = result
        
        # Print raw output
        print(f"📄 RAW TWITTER OUTPUT:")
        print(json.dumps(result, indent=2))
        print("-" * 50)
    
    async def _enrich_linkedin(self, urls: List[str]):
        """Enrich with LinkedIn data"""
        result = await self.tools.run_linkedin_fetch(urls)
        self.person_info["tool_outputs"]["linkedin"] = result
        
        # Print raw output
        print(f"📄 RAW LINKEDIN OUTPUT:")
        print(json.dumps(result, indent=2))
        print("-" * 50)
    
    async def _enrich_serpapi(self, query: str):
        """Enrich with Google search data"""
        result = await self.tools.run_serpapi(query)
        self.person_info["tool_outputs"]["serpapi"] = result
        
        # Print raw output (will be printed in step 4 filtering)
    
    async def _enrich_serpapi_with_key(self, key: str, query: str):
        """Enrich with Google search data using a specific key"""
        result = await self.tools.run_serpapi(query)
        self.person_info["tool_outputs"][key] = result
    
    async def _enrich_firecrawl(self, url: str):
        """Enrich with scraped website data"""
        # Create unique key for each scraped URL
        key = f"firecrawl_{len([k for k in self.person_info['tool_outputs'].keys() if k.startswith('firecrawl')])}"
        result = await self.tools.run_firecrawl(url)
        result["scraped_url"] = url  # Add URL for reference
        self.person_info["tool_outputs"][key] = result
        
        # Print raw output
        print(f"📄 RAW FIRECRAWL OUTPUT ({url}):")
        print(json.dumps(result, indent=2))
        print("-" * 50)
    
    def _extract_twitter_username(self, url: str) -> Optional[str]:
        """Extract Twitter username from URL"""
        match = re.search(r'(?:twitter\.com|x\.com)/([^/\?]+)', url)
        return match.group(1) if match else None

# Main CLI interface
async def main():
    """Main CLI interface for the orchestrator"""
    print("🚀 Person OSINT Orchestrator - Powered by Gemini API")
    print("=" * 60)
    
    try:
        # Get input from user
        name = input("Enter person's name: ").strip()
        phone = input("Enter phone number (with country code): ").strip()
        context_info = input("Enter context information: ").strip()
        
        if not all([name, phone, context_info]):
            print("❌ All fields are required!")
            return
        
        # Create orchestrator and run enrichment
        orchestrator = PersonOSINTOrchestrator()
        
        print(f"\n🔍 Starting OSINT enrichment for: {name}")
        print("=" * 60)
        
        result = await orchestrator.enrich_person(phone, name, context_info)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"osint_result_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ OSINT enrichment completed!")
        print(f"📁 Results saved to: {filename}")
        
        # Display summary
        final_summary = result.get("final_summary", {})
        if final_summary:
            print(f"\n📊 VERIFICATION STATUS: {final_summary.get('verification_status', 'Unknown')}")
            print(f"🎯 CONFIDENCE SCORE: {final_summary.get('confidence_score', 0.0):.2f}")
            
            person_profile = final_summary.get("person_profile", {})
            if person_profile:
                basic_info = person_profile.get("basic_info", {})
                print(f"\n👤 PERSON PROFILE:")
                print(f"   Name: {basic_info.get('name', 'Unknown')}")
                print(f"   Role: {basic_info.get('current_role', 'Unknown')}")
                print(f"   Company: {basic_info.get('company', 'Unknown')}")
                print(f"   Location: {basic_info.get('location', 'Unknown')}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
