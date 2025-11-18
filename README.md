# Person OSINT Orchestrator

A comprehensive person enrichment system that uses multiple OSINT tools orchestrated by Gemini AI to create detailed sales-ready person profiles.

## Features

- **Phone Intelligence**: Validates phone numbers and extracts country information
- **Social Media Enrichment**: Fetches detailed Twitter/X and LinkedIn profiles
- **Web Intelligence**: Google search and website scraping for additional context
- **AI-Powered Analysis**: Gemini API for intelligent parsing, filtering, and summarization
- **Ground Truth Verification**: Validates collected data against original input
- **Sales Intelligence**: Generates talking points and outreach recommendations

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Edit `.env` file and add your Gemini API key:
   ```
   GEMINI_API_KEY = your_actual_gemini_api_key_here
   ```

3. **Verify Other API Keys**:
   Make sure these are properly set in `.env`:
   - `SERPAPI_KEY` - For Google search
   - `NUMVERIFY_KEY` - For phone validation
   - `FIRECRAWLER_API_KEY` - For website scraping
   - `X_API_KEY`, `X_CONSUMER_KEY`, etc. - For Twitter/X access

## Usage

### Interactive Mode
```bash
python orchestrator.py
```

### Test Mode
```bash
python test_orchestrator.py
```

### Programmatic Usage
```python
from orchestrator import PersonOSINTOrchestrator

async def enrich_person():
    orchestrator = PersonOSINTOrchestrator()
    
    result = await orchestrator.enrich_person(
        phone="+1234567890",
        name="John Doe", 
        context_info="Software engineer at Tech Corp, interested in AI"
    )
    
    return result
```

## Input Format

The system expects:
- **Phone Number**: With country code (e.g., "+1234567890")
- **Name**: Full name of the person
- **Context Info**: Any background information about the person, company, or field

## Output Format

The system generates a comprehensive JSON report including:

- **Verification Status**: Whether collected data matches ground truth
- **Person Profile**: Basic info, contact details, professional background
- **Digital Footprint**: Social media activity and online presence
- **Company Context**: Information about their current company
- **Sales Intelligence**: Talking points, pain points, and outreach recommendations
- **Data Sources**: Confidence scores for each information source

## Processing Flow

1. **Phone Validation** - Validates phone and extracts country info
2. **AI Parsing** - Gemini extracts structured data from context
3. **First Wave Enrichment** - Parallel calls to Twitter, LinkedIn, Google search
4. **Link Filtering** - Gemini prioritizes most relevant search results
5. **Second Wave Enrichment** - Scrapes priority websites and profiles
6. **Link Extraction** - Finds additional URLs from social media content
6.5. **Content Parsing** - Gemini intelligently parses all Firecrawl outputs to extract only person-relevant information, filtering out generic company content and unrelated profiles
7. **Final Summary** - Gemini creates comprehensive sales-ready profile

## Tools Integrated

- **NumVerify**: Phone number validation and country detection
- **Twitter/X API**: User profiles and social media activity
- **LinkedIn (BrightData)**: Professional profiles and work history
- **SerpAPI**: Google search results for web presence discovery
- **Firecrawl**: Website content scraping and extraction
- **Gemini (google-genai)**: Intelligent orchestration, parsing, and summarization
- **Telegram (Telethon)**: User client to resolve contacts and chat

## Error Handling

- Graceful degradation if individual tools fail
- Comprehensive logging with timestamps
- Ground truth verification to catch incorrect matches
- Confidence scoring for all data sources

## Privacy & Security

- All API keys stored in environment variables
- Ground truth verification prevents data contamination
- Async processing for better performance
- Detailed audit trail in processing logs

## Example Output

```json
{
  "verification_status": "VERIFIED",
  "confidence_score": 0.85,
  "person_profile": {
    "basic_info": {
      "name": "John Doe",
      "current_role": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA"
    },
    "contact_info": {
      "phone": "+1234567890",
      "linkedin": "https://linkedin.com/in/johndoe",
      "twitter": "@johndoe"
    }
  },
  "sales_intelligence": {
    "talking_points": [
      "Recent AI project at Tech Corp",
      "Interest in machine learning automation",
      "Active in developer community"
    ],
    "best_contact_method": "LinkedIn connection with AI/ML focus"
  }
}
```

## Troubleshooting

1. **API Key Issues**: Ensure all keys in `.env` are valid and have proper permissions
2. **Rate Limits**: The system includes delays and error handling for API rate limits
3. **No Results**: Check if the person has minimal online presence or try different search terms
4. **Verification Failed**: May indicate wrong person found - review ground truth data

## Contributing

Feel free to extend the system by:
- Adding new OSINT tools
- Improving Gemini prompts
- Enhancing error handling
- Adding new output formats

## Telegram Talker

File: `telegram_talker.py`

- Starts a user Telegram client (Telethon) with session `tg_user_session.session`.
- Auth flow: uses `API_ID`, `API_HASH` from `.env` and prompts for phone and login code (2FA supported).
- Resolve a target by `+phone`, `@username`, or name search and prints detailed user info:
  - id, username, first_name, last_name, phone.
- Send messages and listen for replies in terminal.

Usage:

```bash
python telegram_talker.py
```

Notes:
- First run will create a local session file; it is gitignored.
- Respect Telegram ToS and anti-spam rules.

## Package Notes

- Gemini client uses `google-genai` (import style: `from google import genai` and `genai.Client(...).models.generate_content(...)`).
- Firecrawl SDK import is `from firecrawl import Firecrawl`.
- LinkedIn BrightData credentials are read from env: `BRIGHTDATA_API_TOKEN`, optional `BRIGHTDATA_DATASET_ID`.


