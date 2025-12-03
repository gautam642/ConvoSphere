# **Project Canvas: ConvoSphere (MVP)**

## **1\. Core Philosophy & User Flow**

**Philosophy:** ConvoSphere is not a chatbot that talks *to* the client. It is a "Whisperer" that talks *to* the salesperson. It combines static long-term data (OSINT) with dynamic real-time data (Chat Stream) to provide strategic, tactical, and psychological guidance.

**User Flow:**

1. **Initialization:** Salesperson inputs Client Name, Phone/Email, Initial Context, and Sales Goal (e.g., "Sell Enterprise Plan").  
2. **OSINT Execution:** The system orchestrator runs `firecrawl`, `serpapi`, and `linkedin_api` to generate a `Person Profile JSON` (ref: `profiles_by_url_deepti.json`).  
3. **Goal Calibration:** Before the chat starts, the system analyzes the Profile vs. Goal. If the target is "Junior Dev" and the goal is "Sell $50k Package," the system suggests a goal adjustment immediately.  
4. **The Loop (Real-time):**  
   * Salesperson/Client exchange messages.  
   * **Local LLM:** Instantly summarizes context and sentiment.  
   * **RAG Engine:** Fetches similar past winning strategies.  
   * **Gemini Agent:** Analyzes the matrix (Profile \+ Summary \+ RAG) to output real-time coaching, next-message suggestions, and risk flags.  
   * **UI Update:** The dashboard updates widgets (Trust Score, Objections, Next Steps) in real-time.

   ---

   ## **2\. System Architecture & Components**

   ### **A. Input Layer (Salesperson Console)**

* **Inputs:** Client Identifiers, Sales Goal, Real-time Chat Stream.  
* **Function:** Captures raw text and metadata (timestamps).

  ### **B. Intelligence Layer 1: OSINT Orchestrator**

* **Trigger:** On New Chat Creation.  
* **Tools:** `Firecrawl` (Web scraping), `SerpApi` (Google Search), `LinkedIn API`, tweepy (twitter).  
* **Processing:** Raw data is cleaned and structured.  
* **Output:** `client_profile.json`.  
  * *Note:* Uses the structure provided in your file (Experience, Activity, About, Location) to derive "Psychological Hooks" (e.g., "Active on LinkedIn regarding AI ethics" \-\> Hook: Discuss AI safety).  
  * Output will be structured in key:value to style \- detailing the characteristics of the person across various things, fields , categories necessary for sales knowledge decision \- making.

  ### **C. Intelligence Layer 2: Local LLM (Tactical Analyst)**

* **Model:** Llama-3-8B-Instruct or Mistral-7B (Quantized for speed).  
* **Trigger:** Every new message block.  
* **Input:** `Global Summary` (prev of conversation till trigger), `New Raw Messages`.  
* **Output:** `Tactical_JSON`  
  JSON  
  {

   "global\_summary": "Updated abstract of full conversation.",  "latest\_interaction\_summary": "Client asked about pricing, User deflected.",  "current\_sentiment": "Skeptical but curious",  "conversation\_state\_tag": "Price\_Negotiation"

  }

  ### **D. Intelligence Layer 3: RAG Engine (The Knowledge Base)**

* **Vector DB:** ChromaDB or Pinecone.  
* **Trigger:** Parallel with Local LLM.  
* **Query 1 (Profile Match):** "Find past clients with similar Job Title \+ Industry \+ Company Size." \-\> *Retrieve successful conversation patterns.*  
* **Query 2 (Goal Match):** "Find past conversations where goal was 'Sell X'." \-\> *Retrieve common objections and closing techniques.*  
* **Output:** `rag_context_string` (e.g., "In 80% of similar profiles, emphasizing 'Time Saving' worked better than 'Cost Saving'.").

  ### **E. Intelligence Layer 4: Gemini API (The Strategic Coach)**

This is the core decision-maker.

* **Trigger:** after local llm processing and 3-5 seconds passed since last client reply. If new client reply comes reset timer. Timer implies client’s done talking.  
* **Input:**  
  1. `client_profile.json`  
  2. `Tactical_JSON` (from Local LLM)  
  3. `rag_context_string`  
  4. `Sales_Goal`  
  5. `Raw_Last_10_Messages`  
* **Output:** A complex JSON object driving the UI (detailed in Section 3).  
  ---

  ## **3\. Detailed Feature Specifications (Gemini Output Goals)**

The Gemini prompt must be structured to return a JSON object containing these specific analysis blocks:

### **1\. State & Mode Detection**

* **Sales Stage Classifier:** Identify current stage: *Initializing, Rapport Building, Needs Discovery, Solution Pitching, Objection Handling, Closing, Stall/Delay, Dead.*  
* **Client Mode Detector:**  
  * *Buying Mode:* (High intent, asks about implementation).  
  * *Validation Mode:* (Comparing features, rational).  
  * *Argumentative Mode:* (Nitpicking, emotional).  
  * *Delaying Mode:* (Vague answers, "send me an email").  
* **Competitor Flag:** Boolean. If `True`, identify which competitor and suggest a "Kill Sheet" point (e.g., "They mentioned Competitor X; Note that X lacks feature Y").

  ### **2\. Sales Coaching & Quality Control**

* **Salesperson Critique:**  
  * *Passive/Pushy Check:* "You are being too aggressive given their hesitation."  
  * *Relevance Check:* "Client asked about security; you answered about speed. Re-align."  
* **Red Flag Detector:**  
  * *Fake Interest:* "Client keeps agreeing but offers no specific details."  
  * *Authority Gap:* "Client implies they need to 'ask the boss'—they are not the decision maker."

  ### **3\. Personalization & Strategic Hooks (The "OSINT Magic")**

* **Bio-Hooks:** (likings , interests and potential pain points in professional/personal life)"Client liked a post about 'AI in Healthcare' yesterday. Mention how our tool ensures HIPAA compliance." (Derived from age, gender, job, company, `activity` list in `profiles_by_url_deepti.json`).  
* **Authority/Budget Prediction:** "Based on 'Director' title and 'Jaypee Institute' context, they likely have decision power but a strict academic budget cycle."  
* **Timing Suggestion:** "Academic profile. Do not call between 9 AM \- 2 PM (Lectures). Suggest 4 PM."

  ### **4\. The Tracker (B.A.N.T. & Objections)**

* **BANT Tracker:**  
  * *Budget:* (Unknown / $X / Flexible)  
  * *Authority:* (Gatekeeper / Influencer / Decision Maker)  
  * *Need:* (Identified: X, Y)  
  * *Timeline:* (Q4 / Immediate / Next Year)  
* **Objection Prediction Matrix:**  
  * *Upcoming Risk:* "High probability of 'Integration Complexity' objection."  
  * (give out list of most probable objections coming up, with each probability and resolution/resterring conversation msgs/stratergy.  
  * *Handling Strategy:* "Pre-empt this by sharing the API documentation link now."

  ### **5\. Actionable Outputs (The "Next Step")**

* **Suggested next msg:** A ready-to-send tailored response using NLP suitable for the client's tone.  
* **Suggested follow-up question(s) to Ask:** "Ask: 'How are you currently handling \[Pain Point\]?'"  
* **Closing Trigger:** If stage is *Closing*, suggest: "Ask for the PO now. Confidence score: 85%."  
  ---

  ## **4\. MVP Data Schema (JSON Output from Gemini)**

This is the contract between the AI and the Frontend UI.

JSON

* {  
*   "meta": {  
*     "timestamp": "2025-11-21T18:05:00",  
*     "confidence\_score": 0.88  
*   },  
*   "analysis": {  
*     "current\_stage": "Needs Discovery",  
*     "client\_mode": "Validation Mode",  
*     "competitor\_detected": false,  
*     "red\_flags": \["Unclear Authority"\],  
*     "salesperson\_critique": "Good conversational flow, but you missed their question about integration."  
*   },  
*   "tracker": {  
*     "trust\_level": "Medium-High",  
*     "pain\_points\_discovered": \["Manual data entry", "Slow reporting"\],  
*     "budget\_clarity": "Low",  
*     "authority\_status": "Influencer (Need to find Decision Maker)"  
*   },  
*   "strategy": {  
*     "suggested\_next\_message": "That makes sense. Regarding integration, we support native SQL drivers. Does your team currently use asyncpg for database interactions?",  
*     "suggested\_question": "Who else on your team would need to sign off on a pilot?",  
*     "personal\_hook": "I noticed your research involves high-latency networks; our system is optimized specifically for that.",  
*     "timing\_suggestion": "Send follow-up email tomorrow at 11:00 AM."  
*   },  
*   "objections": {  
*     "predicted\_next": "Pricing",  
*     "probability": 0.75,  
*     "preemptive\_tactic": "Mention ROI and time-savings before dropping the price."  
*   }  
* }  
    
  ---

  ## **5\. RAG Implementation Details (Memory)**

To make the system "Smart," it needs to learn from the past.

1. **Vector Embedding:**  
   * Embed `Client Profile Summary` \+ `Sales Goal`.  
   * Embed `Successful Conversation Transcripts` (chunked).  
2. **Retrieval Logic:**  
   * When a new chat starts with "Dr. Deepti Singh" (Academic, CS Background), the RAG searches for: `tags:[Academic, Computer Science, Decision Maker] AND status:[Deal Closed]`.  
   * It extracts the *strategies* used in those retrieved chats (e.g., "Detailed technical specs won the deal").  
3. **Failure Analysis:**  
   * Fetch `status:[Deal Lost]` for similar profiles.  
   * Extract *warnings* (e.g., "Pushing for a contract too early killed the deal with Academics").

   ---

   ## **6\. Impact & Value Proposition**

* **Reduced Ramp-up Time:** Junior salespeople perform like seniors because Gemini guides the strategy.  
* **Hyper-Personalization:** Using OSINT (e.g., knowing they just published a paper) builds instant rapport, which is statistically shown to increase conversion.  
* **Saved Deals:** The "Red Flag" and "Sentiment Analysis" catch a souring mood before the salesperson realizes it, allowing for course correction.  
* **CRM Automation:** The `tracker` JSON can auto-fill the CRM (Salesforce/HubSpot) after the chat, saving manual entry time.

  