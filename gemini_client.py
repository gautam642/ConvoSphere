import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from google import genai
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    """Client for Gemini API interactions"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # genai.configure(api_key=api_key)
        self.client = genai.Client(api_key=api_key)
    
    async def parse_initial_info(self, name: str, phone: str, context_info: str, country_info: Dict) -> Dict[str, Any]:
        """Step 2: Parse initial person info and generate search query"""
        prompt = f"""
You are an expert OSINT analyst. Parse the following information about a person and extract structured data.

PERSON INFO:
- Name: {name}
- Phone: {phone}
- Context: {context_info}
- Phone Country Info: {json.dumps(country_info, indent=2)}

TASK: Extract and structure the following information in JSON format:

1. **links_mentioned**: List of any URLs or links mentioned (LinkedIn, Twitter, GitHub, personal sites, etc.)
2. **usernames_mentioned**: Dict with platform as key and username as value (twitter, linkedin, github, etc.)
3. **company_info**: Any company names, roles, or business context mentioned
4. **background_info**: Education, field of work, expertise areas mentioned
5. **personal_details**: Age, gender, location if mentioned
6. **other_context**: Any other relevant information
7. **google_search_query_to_get_linkedin_profile**: A human like structured Google search query like a salesperson 
        would write on google given the information like you are given to get linkedIN associated to the person
8. **google_search_to_get_usernames_links_queries**: A human like structured Google search queries list [] like a salesperson 
        would write on google given the information like you are given to get respective username's platform link...(for all usernames/platforms
        found or hinted in the information/Context or should most probably exist given persons profile background)(dont't mention linkedin again in these queries)
9. **google_search_query_to_get_company_profile**: A human like structured Google search query like a salesperson 
        would write on google given the information like you are given to get company's details of the person.
10. **google_search_generic_query**: A human like structured Google search query like a salesperson 
        would write on google given the information like you are given to get general information links of the person (dont include username/platform keywords in this query)

OUTPUT ONLY VALID JSON in this format:
{{
    "links_mentioned": ["url1", "url2", etc...],
    "usernames_mentioned": {{"twitter": "username", "linkedin": "profile-name" etc...}},
    "company_info": {{"current_company": "name", "role": "title", "industry": "field" etc...}},
    "background_info": {{"education": "details", "expertise": ["area1", "area2"] etc...}},
    "personal_details": {{"age": null, "gender": null, "location": "city, country" etc...}},
    "other_context": "summary of other relevant info",
    "google_search_query_to_get_linkedin_profile": "optimized search query for finding person's linkedin profile",
    "google_search_to_get_usernames_links_queries": ["query1", "etc..."],
    "google_search_query_to_get_company_profile": "optimized search query for finding person's company profile",
    "google_search_generic_query": "optimized search query for finding person's information available online"
    
}}
"""
        
        try:
            print("🤖 Gemini: Parsing initial person information...")
            response = await asyncio.to_thread(self.client.models.generate_content, model="gemini-2.5-flash", contents=prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            parsed_data = json.loads(response_text)
            print("✅ Gemini: Initial parsing completed")
            return parsed_data
            
        except Exception as e:
            print(f"❌ Gemini parsing error: {str(e)}")
            return {
                "links_mentioned": [],
                "usernames_mentioned": {},
                "company_info": {},
                "background_info": {},
                "personal_details": {},
                "other_context": context_info,
                "google_search_query_to_get_linkedin_profile": f'"{name}" profile linkedin',
                "google_search_to_get_usernames_links_queries": [f'"{name}" twitter', f'"{name}" github'],
                "google_search_query_to_get_company_profile": f'"{name}" company profile',
                "google_search_generic_query": f'"{name}" profile'
            }
    
    async def filter_search_links(self, person_info: Dict, search_results: Dict) -> List[str]:
        """Step 4: Filter and prioritize links from search results"""
        prompt = f"""
You are an expert OSINT analyst. Given person information and multiple Google search results from different queries, identify the TOP 5 most relevant links that should be investigated further with web scraping.

PERSON INFO:
{json.dumps(person_info, indent=2)}

MULTIPLE SEARCH RESULTS (from different search strategies):
{json.dumps(search_results, indent=2)}

TASK: Analyze ALL the search results from different queries and return the TOP 5 most relevant URLs that are likely to contain valuable information about this specific person. Prioritize:
1. LinkedIn profiles
2. Twitter/X profiles  
3. Other social profiles
4. Personal websites/portfolios
5. Company pages where they work
6. GitHub profiles
7. News articles or interviews
8. Academic/professional profiles
9. University/institution pages

IMPORTANT: 
- Verify the links seem to match the person based on name, company, location, context
- Avoid duplicate or very similar URLs
- Only return URLs that would benefit from web scraping
- Focus on pages that likely contain biographical/professional information

OUTPUT ONLY a JSON array of exactly 5 URLs:
["url1", "url2", "url3", "url4", "url5"]
"""
        
        try:
            print("🤖 Gemini: Filtering search results...")
            response = await asyncio.to_thread(self.client.models.generate_content, model="gemini-2.5-flash", contents=prompt)
            
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            filtered_links = json.loads(response_text)
            print(f"✅ Gemini: Filtered to {len(filtered_links)} priority links")
            return filtered_links
            
        except Exception as e:
            print(f"❌ Gemini link filtering error: {str(e)}")
            # Fallback: extract first 5 URLs from all search results
            fallback_links = []
            combined_searches = search_results.get("combined_searches", {})
            
            for search_key, search_data in combined_searches.items():
                if search_data.get("success") and search_data.get("data"):
                    organic = search_data["data"].get("organic_results", [])
                    for result in organic:
                        if result.get("link") and len(fallback_links) < 5:
                            fallback_links.append(result["link"])
            
            return fallback_links[:5]
    
    async def verify_and_summarize(self, ground_truth: Dict, all_collected_data: Dict) -> Dict[str, Any]:
        """Step 7-8: Verify against ground truth and create final summary"""
        prompt = f"""
You are an expert OSINT analyst creating a comprehensive person profile for sales purposes.

GROUND TRUTH (Original Input):
{json.dumps(ground_truth, indent=2)}

COLLECTED DATA FROM TOOLS:
{json.dumps(all_collected_data, indent=2)}

TASK: Create a comprehensive sales-ready person profile. Verify all information against the ground truth and flag any major discrepancies.

VERIFICATION RULES:
- If collected data contradicts ground truth significantly (different person, company, location), mark as "VERIFICATION_FAILED"
- If data seems consistent or complementary, mark as "VERIFIED"
- Include confidence scores for each data source

OUTPUT JSON format:
{{
    "verification_status": "VERIFIED" or "VERIFICATION_FAILED",
    "confidence_score": 0.0-1.0,
    "discrepancies": ["list of any major conflicts found"],
    "person_profile": {{
        "basic_info": {{
            "name": "full name",
            "current_role": "job title",
            "company": "current company",
            "location": "city, country",
            "industry": "field/industry"
        }},
        "contact_info": {{
            "phone": "verified phone",
            "email": "found emails",
            "linkedin": "linkedin url",
            "twitter": "twitter handle",
            "other_profiles": ["other social/professional profiles"]
        }},
        "professional_background": {{
            "experience": ["previous roles/companies"],
            "education": "educational background",
            "skills": ["key skills/expertise"],
            "achievements": ["notable accomplishments"]
        }},
        "digital_footprint": {{
            "social_media_activity": "summary of online presence",
            "content_themes": ["topics they post/talk about"],
            "engagement_level": "how active they are online",
            "influence_metrics": "follower counts, engagement rates"
        }},
        "company_context": {{
            "company_description": "what their company does",
            "company_size": "estimated size/stage",
            "industry_trends": "relevant industry context",
            "potential_pain_points": ["likely business challenges"]
        }}
    }},
    "sales_intelligence": {{
        "talking_points": ["5 specific conversation starters"],
        "pain_points": ["likely business/personal challenges"],
        "interests": ["personal/professional interests"],
        "best_contact_method": "recommended approach",
        "timing_insights": "best time/context to reach out"
    }},
    "data_sources": {{
        "linkedin": {{"confidence": 0.0-1.0, "key_insights": ["insights"]}},
        "twitter": {{"confidence": 0.0-1.0, "key_insights": ["insights"]}},
        "web_search": {{"confidence": 0.0-1.0, "key_insights": ["insights"]}},
        "scraped_content": {{"confidence": 0.0-1.0, "key_insights": ["insights"]}}
    }}
}}
"""
        
        try:
            print("🤖 Gemini: Creating final verification and summary...")
            response = await asyncio.to_thread(self.client.models.generate_content, model="gemini-2.5-flash", contents=prompt)
            
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            final_summary = json.loads(response_text)
            print("✅ Gemini: Final summary completed")
            return final_summary
            
        except Exception as e:
            print(f"❌ Gemini summary error: {str(e)}")
            return {
                "verification_status": "ERROR",
                "confidence_score": 0.0,
                "error": str(e),
                "person_profile": {},
                "sales_intelligence": {},
                "data_sources": {}
            }
    
    async def parse_scraped_content(self, scraped_data: Dict, person_info: Dict, ground_truth: Dict) -> Dict[str, Any]:
        """Parse and extract relevant information from Firecrawl scraped content"""
        
        # Extract the actual content from Firecrawl response
        content = ""
        if scraped_data.get("success") and scraped_data.get("data"):
            firecrawl_data = scraped_data["data"]
            if isinstance(firecrawl_data, str):
                # If data is a JSON string, parse it
                try:
                    firecrawl_data = json.loads(firecrawl_data)
                except:
                    pass
            
            # Extract content from various possible fields
            if isinstance(firecrawl_data, dict):
                content = firecrawl_data.get("markdown", "") or firecrawl_data.get("content", "") or firecrawl_data.get("text", "")
            else:
                content = str(firecrawl_data)
        
        # Limit content length to avoid token limits
        if len(content) > 8000:
            content = content[:8000] + "... [truncated]"
        
        scraped_url = scraped_data.get("scraped_url", "unknown")
        
        prompt = f"""
You are an expert OSINT analyst. Parse the following scraped website content and extract ONLY information that is relevant to the target person.

GROUND TRUTH (Target Person):
{json.dumps(ground_truth, indent=2)}

CURRENT PERSON INFO COLLECTED:
{json.dumps(person_info, indent=2)}

SCRAPED URL: {scraped_url}

SCRAPED CONTENT:
{content}

TASK: Extract ONLY information that is clearly about the target person. Ignore generic company info, other people's profiles, or unrelated content.

VERIFICATION RULES:
1. Name must match or be very similar to ground truth name
2. Company/role should align with known information
3. Location should be consistent if mentioned
4. If this content is about a different person, return "not_target_person": true

OUTPUT JSON format:
{{
    "not_target_person": false,
    "relevance_score": 0.0-1.0,
    "extracted_info": {{
        "personal_details": {{
            "name_variations": ["any name variations found"],
            "titles": ["job titles mentioned"],
            "bio": "relevant bio/about information",
            "location": "location if mentioned",
            "contact_info": ["emails, phones, social handles found"]
        }},
        "professional_info": {{
            "current_role": "current position",
            "company": "company name",
            "experience": ["previous roles/companies"],
            "skills": ["technical skills, expertise areas"],
            "achievements": ["notable accomplishments"],
            "projects": ["projects or work mentioned"]
        }},
        "interests_and_content": {{
            "topics": ["subjects they discuss/write about"],
            "expertise_areas": ["areas of expertise"],
            "recent_activity": ["recent posts, articles, updates"],
            "speaking_engagements": ["conferences, talks, interviews"]
        }},
        "additional_links": ["any other social/professional profiles found"],
        "key_quotes": ["important quotes or statements by the person"],
        "company_context": {{
            "company_description": "what their company does",
            "company_role": "their role/department",
            "team_info": "team or department details"
        }}
    }},
    "confidence_notes": "explanation of why this content is/isn't about the target person"
}}

If the content is clearly not about the target person or contains no relevant information, set "not_target_person": true and "relevance_score": 0.0.
"""
        
        try:
            print(f"🤖 Gemini: Parsing scraped content from {scraped_url}")
            response = await asyncio.to_thread(self.client.models.generate_content, model="gemini-2.5-flash", contents=prompt)
            
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            parsed_content = json.loads(response_text)
            
            relevance_score = parsed_content.get("relevance_score", 0.0)
            is_target = not parsed_content.get("not_target_person", False)
            
            print(f"✅ Gemini: Content parsing completed - Relevance: {relevance_score:.2f}, Target Person: {is_target}")
            return parsed_content
            
        except Exception as e:
            print(f"❌ Gemini content parsing error: {str(e)}")
            return {
                "not_target_person": True,
                "relevance_score": 0.0,
                "extracted_info": {},
                "confidence_notes": f"Parsing failed: {str(e)}"
            }
