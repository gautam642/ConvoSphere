from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from datetime import datetime
from schemas import CreateSessionRequest, Session, Message, OSINT, LocalLLMAnalysis, GeminiAnalysis, Alert, NewMessageRequest, SendMessageRequest
from db.database import get_mongo_client, get_redis_client, get_sessions_collection, connect_to_mongo, close_mongo_connection
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
import pymongo
from typing import Optional, Dict, Any, List
import asyncio
import json # For json.dumps

# Import services
from services.telegram_router import TelegramRouter
from gemini_client import GeminiClient # Still using the old gemini_client.py
from services.local_llm_service import get_llm_service, LocalLLMService
from services.connection_manager import ConnectionManager # Import ConnectionManager
from fastapi.middleware.cors import CORSMiddleware
from orchestrator import PersonOSINTOrchestrator

app = FastAPI(
    title="ConvoSphere API",
    description="API for the ConvoSphere OSINT-Powered Sales Intelligence System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow the React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager() # Instantiate ConnectionManager here

# Initialize services globally
telegram_router: Optional[TelegramRouter] = None # Will be initialized on startup
gemini_client_instance = GeminiClient() # Rename to avoid conflict if gemini_client.py becomes a service
local_llm_service = get_llm_service() # Get instance of LocalLLMService


# --- Background Tasks / Workers ---

# Placeholder for Alert Dispatcher
async def run_alert_dispatcher(session_id: str, alert_data: Dict[str, Any], db: AsyncIOMotorDatabase):
    sessions_collection = db["sessions"]
    print(f"--- Dispatching alert for session {session_id}: {alert_data.get('message')} ---")
    
    new_alert = Alert(**alert_data)
    
    await sessions_collection.update_one(
        {"_id": session_id},
        {
            "$push": {"alerts": new_alert.dict(exclude_none=True)},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    print(f"--- Alert saved for session {session_id} ---")


# OSINT enrichment function using PersonOSINTOrchestrator
async def run_osint_enrichment(session_id: str, db: AsyncIOMotorDatabase):
    sessions_collection = db["sessions"]
    print(f"--- Starting OSINT enrichment for session: {session_id} ---")
    
    try:
        # Fetch session document
        session_doc = await sessions_collection.find_one({"_id": session_id})
        if not session_doc:
            print(f"OSINT enrichment failed: Session {session_id} not found.")
            return
        
        # Update status to processing
        await sessions_collection.update_one(
            {"_id": session_id},
            {"$set": {"osint.status": "processing", "updated_at": datetime.utcnow()}}
        )
        
        # Extract customer data
        customer = session_doc.get('customer', {})
        phone = customer.get('phone', '')
        name = customer.get('name', '')
        context_info = customer.get('context', '')
        
        if not phone or not name:
            print(f"OSINT enrichment failed: Missing phone or name for session {session_id}")
            await sessions_collection.update_one(
                {"_id": session_id},
                {"$set": {"osint.status": "failed", "osint.error": "Missing required customer data", "updated_at": datetime.utcnow()}}
            )
            return
        
        # Run the orchestrator
        orchestrator = PersonOSINTOrchestrator()
        result = await orchestrator.enrich_person(phone, name, context_info)
        
        # Save the enrichment result to the session
        await sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "osint.status": "completed",
                    "osint.data": result,
                    "osint.completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        print(f"--- OSINT enrichment completed successfully for session: {session_id} ---")
        
    except Exception as e:
        print(f"OSINT enrichment error for session {session_id}: {type(e).__name__}: {e}")
        await sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "osint.status": "failed",
                    "osint.error": str(e),
                    "updated_at": datetime.utcnow()
                }
            }
        )


# Local LLM Analyze Worker
async def run_local_llm_analyze(session_id: str, db: AsyncIOMotorDatabase, background_tasks: BackgroundTasks):
    with open("debug_api.txt", "a") as f:
        f.write(f"run_local_llm_analyze called for {session_id}\n")
    try:
        print("--- Starting Local LLM analysis... ---")
        sessions_collection = db["sessions"]
        print(f"--- Starting Local LLM analysis for session: {session_id} ---")

        session_doc = await sessions_collection.find_one({"_id": session_id})
        if not session_doc:
            print(f"Local LLM analysis failed: Session {session_id} not found.")
            return

        session = Session.model_validate(session_doc)
    
        # Prepare payload for Local LLM Service
        llm_payload = {
            "session_id": session.session_id,
            "customer": session.customer.dict() if session.customer else {},
            # "osint": session.osint.dict() if session.osint else {},
            "short_context": [
                {**msg.dict(), "timestamp": msg.timestamp.isoformat()}
                for msg in session.messages
            ],
            "goal": session.customer.goal if session.customer else None,
            "task": "analyze_and_summarize"
        }

        try:
            analysis_result = await local_llm_service.analyze(llm_payload)
            
            # --- Save LLM result to a file for analysis ---
            serializable_result = analysis_result.copy()
            if 'last_analysis_at' in serializable_result and isinstance(serializable_result['last_analysis_at'], datetime):
                serializable_result['last_analysis_at'] = serializable_result['last_analysis_at'].isoformat()
            
            with open("llm_analysis_result.json", "w") as f:
                json.dump(serializable_result, f, indent=2)
            print("--- Saved LLM analysis result to llm_analysis_result.json ---")
            # --- End of save block ---

            # Update session with the new structured LLM analysis
            await sessions_collection.update_one(
                {"_id": session_id},
                {"$set": {"local_llm": analysis_result, "updated_at": datetime.utcnow()}}
            )
            print(f"--- Local LLM analysis completed and session updated for {session_id} ---")

            updated_session_doc = await sessions_collection.find_one({"_id": session_id})
            if updated_session_doc:
                session_to_broadcast = Session.model_validate(updated_session_doc)
                await manager.send_session_update(session_id, session_to_broadcast.model_dump(mode='json'))

                # --- Conditional Gemini Triggering ---
                should_trigger_gemini = False
                trigger_reason = ""
                
                # Condition: Trigger after EVERY customer reply
                # Check if the last message in the session is from the customer
                if session_to_broadcast.messages and session_to_broadcast.messages[-1].sender == "customer":
                    should_trigger_gemini = True
                    trigger_reason = "customer_reply"
                
                if should_trigger_gemini:
                    print(f"--- Triggering Gemini due to: {trigger_reason} ---")
                    # Trigger Gemini with a default strategic review task
                    background_tasks.add_task(run_gemini_call, session_id, "Strategic Review", db)

        except Exception as e:
            print(f"--- Error in conditional Gemini trigger: {e} ---")
            with open("debug_error.txt", "a") as f:
                f.write(f"Error in conditional Gemini trigger: {e}\n")

    except Exception as e:
        import traceback
        error_msg = f"CRITICAL ERROR in run_local_llm_analyze for session {session_id}: {e}\n{traceback.format_exc()}"
        print(error_msg)
        with open("debug_error.txt", "a") as f:
            f.write(error_msg + "\n")
        
        # Try to update status if possible
        try:
            await sessions_collection.update_one(
                {"_id": session_id},
                {"$set": {"local_llm.error": str(e), "updated_at": datetime.utcnow()}}
            )
        except:
            pass

    print("--- Finished Local LLM analysis. ---")


# Gemini call worker
async def run_gemini_call(session_id: str, task: str, db: AsyncIOMotorDatabase):
    sessions_collection = db["sessions"]
    print(f"--- Starting Gemini call for session: {session_id}, task: {task} ---")

    session_doc = await sessions_collection.find_one({"_id": session_id})
    if not session_doc:
        print(f"Gemini call failed: Session {session_id} not found.")
        return

    session = Session.model_validate(session_doc)
    
    # Extract OSINT final_summary from session
    osint_data = {}
    if session.osint and session.osint.data:
        # Use the final_summary from the enriched OSINT data
        osint_data = session.osint.data.get('final_summary', {})
        print(f"--- Using OSINT final_summary for Gemini analysis ---")
    else:
        print(f"--- Warning: No OSINT data available for session {session_id} ---")

    # Construct Gemini payload
    gemini_payload = {
        "session_id": session.session_id,
        "customer": session.customer.model_dump(mode='json') if session.customer else {},
        "osint": osint_data,  # Now contains final_summary with person_profile, sales_intelligence, etc.
        "short_context": [msg.model_dump(mode='json') for msg in session.messages[-10:]], 
        "local_llm_analysis": session.local_llm.model_dump(mode='json') if session.local_llm else {},
        "task": task # The user's prompt from the Gemini chat pane
    }

    try:
        # Check if this is a user query or auto-triggered strategic review
        is_user_query = task and task != "Strategic Review"
        
        if is_user_query:
            # User asked a specific question - answer it directly
            prompt = f"""
# ROLE
You are an elite Sales Strategist and AI Assistant helping a salesperson during a live negotiation.

# USER'S QUESTION
{task}

# CONTEXT DATA
{json.dumps(gemini_payload, indent=2)}

# INSTRUCTIONS
Answer the user's question directly and concisely using the context provided. Focus on:
1. Directly addressing their specific question
2. Using OSINT data (person_profile, sales_intelligence, company_context) to provide personalized insights
3. Referencing the conversation history if relevant
4. Providing actionable advice

Keep your response clear, practical, and under 300 words.

# OUTPUT FORMAT
Provide your answer as a JSON object with this structure:
{{
  "answer": "Your direct answer to the user's question",
  "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
  "suggested_action": "One specific action the salesperson should take"
}}
"""
        else:
            # Auto-triggered strategic review - use structured analysis
            prompt = f"""
# ROLE AND OBJECTIVE

You are an elite Sales Strategist and Psychological Coach. Your goal is to assist a human salesperson in real-time during a live negotiation. You do not speak to the customer directly. Instead, you "whisper" strategic advice, psychological insights, and drafted responses to the salesperson to help them close the deal.



# INPUT CONTEXT DATA
{json.dumps(gemini_payload, indent=2)}


# ANALYSIS INSTRUCTIONS

You must analyze the inputs and generate a JSON output based on the following logic:

## 1. State & Mode Detection
- *Sales Stage*: Classify the conversation into exactly one of: [Initializing, Rapport Building, Needs Discovery, Solution Pitching, Objection Handling, Closing, Stall/Delay, Dead].
- *Client Mode*: Detect the client's psychological state:
  - Buying Mode: High intent, asking about implementation/pricing.
  - Validation Mode: Rational, comparing features, asking "how".
  - Argumentative Mode: Emotional, nitpicking, defensive.
  - Delaying Mode: Vague, avoiding commitment ("send me an email").
- *Competitor Flag*: If the client mentions a competitor, set to true and provide a specific counter-point in the strategy section. search about the client and suggest a counter point.

## 2. Quality Control & Critique
- *Passive/Pushy Check*: Warn if the salesperson is being too aggressive (pushy) or failing to lead the frame (passive).
- *Red Flag Detector*: Identify risks such as "Fake Interest" (agreeing without detail) or "Authority Gap" (implies they need boss's approval).

## 3. OSINT & Personalization (Crucial)
- *Bio-Hooks: Analyze the **Client Profile (OSINT)* to find personal connections, relevant pointers to talk through/about to steer client conversation towards the goal.
  - Timing: Use their location/job role to judge if now is a good time to call (e.g., "Don't call Academics during lecture hours").

## 4. B.A.N.T. Tracker
Extract the following from context (if available):
- *Budget*: Unknown / Flexible / Specific Amount. (comparative analysis of client's possible income to the goal's pricing, suggest goal adjustment based on the analysis).
- *Authority*: Gatekeeper / Influencer / Decision Maker.
- *Need*: Specific pain points mentioned.
- *Timeline*: Quarter / Immediate / Next Year.

## 5. Actionable Strategy (The "Next Step")
- *Draft Response*: Write a ready-to-send reply for the salesperson. It must use NLP suitable for the salesperson's current tone (mirroring).
- *Closing Trigger*: If current_stage is "Closing", suggest asking for the Purchase Order (PO) immediately.

# OUTPUT FORMAT
You must output *ONLY* a valid JSON object matching the schema below. Do not include markdown formatting or explanations outside the JSON.

```json
{{
  "meta": {{
    "timestamp": "{datetime.utcnow().isoformat()}",
    "confidence_score": 0.00  // Float 0.0 to 1.0 representing confidence in this advice
  }},
  "analysis": {{
    "current_stage": "String (One of the defined stages)",
    "client_mode": "String (Buying/Validation/Argumentative/Delaying)",
    "competitor_detected": false or true // Boolean
    "red_flags": ["String", "String"], // List of detected risks like 'Unclear Authority'
    "salesperson_critique": "String (Advice to the agent on their tone/approach)"
  }},
  "tracker": {{
    "trust_level": "String (Low/Medium/High)",
    "pain_points_discovered": ["String", "String"],
    "budget_clarity": "String (Low/Medium/High)",
    "authority_status": "String (Gatekeeper/Influencer/Decision Maker)"
  }},
  "strategy": {{
    "suggested_next_message": "String (The exact text the agent should send, dont make it too long)",
    "suggested_question": "String (A follow-up question to deepen discovery and/or conversation sterring to wards goal)",
    "personal_hook": "String (Context-aware hook based on OSINT/Bio)",
    "timing_suggestion": "String (e.g., 'Send follow-up email tomorrow at 11:00 AM')"
  }},
  "objections": {{
    "predicted_next": "String (The most likely objection to come next, e.g., 'Pricing') based on the cues already given by salesperson and conversation going.",
    "probability": 0.00, // Float 0.0 to 1.0
    "preemptive_tactic": "String (How to handle it before it arises)"
  }}
}}
```
"""
        
        response_text = await gemini_client_instance.generate_content(prompt)
        
        print(f"--- Gemini raw response (first 500 chars): {response_text[:500]} ---")
        
        # Parse the JSON response
        parsed_json = {}
        try:
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            parsed_json = json.loads(cleaned_text)
            print(f"--- Gemini JSON parsed successfully. Keys: {list(parsed_json.keys())} ---")
        except json.JSONDecodeError as e:
            print(f"--- Gemini JSON parse error: {e} ---")
            print(f"--- Cleaned text (first 500 chars): {cleaned_text[:500]} ---")
            parsed_json = {"error": "Failed to parse JSON", "raw_response": response_text[:10000]}

        gemini_result = {
            "last_call_at": datetime.utcnow(),
            "payload_sent": gemini_payload,
            "response": parsed_json, # Store the parsed JSON
            "query_type": "user_query" if is_user_query else "strategic_review",  # Track the type
            "user_query": task if is_user_query else None  # Store the original question
        }

        await sessions_collection.update_one(
            {"_id": session_id},
            {"$set": {"gemini": gemini_result, "updated_at": datetime.utcnow()}}
        )
        print(f"--- Gemini call completed for session: {session_id} ---")

        # Broadcast the final update
        updated_session_doc = await sessions_collection.find_one({"_id": session_id})
        if updated_session_doc:
            session_to_broadcast = Session.model_validate(updated_session_doc)
            await manager.send_session_update(session_id, session_to_broadcast.model_dump(mode='json'))

    except Exception as e:
        print(f"--- Gemini call failed for session {session_id}: {e} ---")
        await sessions_collection.update_one(
            {"_id": session_id},
            {"$set": {"gemini.error": str(e), "updated_at": datetime.utcnow()}}
        )
        # Broadcast the error update
        updated_session_doc = await sessions_collection.find_one({"_id": session_id})
        if updated_session_doc:
            session_to_broadcast = Session.model_validate(updated_session_doc)
            await manager.send_session_update(session_id, session_to_broadcast.model_dump(mode='json'))


# --- FastAPI Event Handlers ---

@app.on_event("startup")
async def startup_event():
    global telegram_router
    await connect_to_mongo()
    db = await get_mongo_client()
    telegram_router = TelegramRouter(db=db, manager=manager)
    await telegram_router.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    await telegram_router.disconnect()


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"--- WebSocket disconnected for session: {session_id} ---")

# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to ConvoSphere API", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/sessions", response_model=Session, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def create_session(
    request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_mongo_client),
    sessions_collection: AsyncIOMotorCollection = Depends(get_sessions_collection)
):
    session_data = {
        "customer": request.dict(),
        "owner": request.owner_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "osint": {},
        "local_llm": {},
        "gemini": {},
        "messages": [],
        "alerts": [],
        "status": "initialized"
    }
    
    new_session_obj = Session.model_validate(session_data)
    
    try:
        await sessions_collection.insert_one(new_session_obj.model_dump(by_alias=True))
        
        background_tasks.add_task(run_osint_enrichment, new_session_obj.session_id, db)
        
        return new_session_obj
            
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

@app.get("/api/sessions", response_model=List[Session], response_model_by_alias=False)
async def list_sessions(
    sessions_collection: AsyncIOMotorCollection = Depends(get_sessions_collection)
):
    try:
        sessions_cursor = sessions_collection.find({})
        sessions = await sessions_cursor.to_list(length=100)
        return sessions
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

    try:
        sessions_cursor = sessions_collection.find({})
        sessions = await sessions_cursor.to_list(length=100)
        return sessions
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

@app.get("/api/sessions/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_client),
    sessions_collection: AsyncIOMotorCollection = Depends(get_sessions_collection)
):
    try:
        session = await sessions_collection.find_one({"_id": session_id})
        if session:
            return Session.model_validate(session)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID {session_id} not found")
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")


@app.post("/api/sessions/{session_id}/messages", response_model=Session)
async def add_message_to_session(
    session_id: str,
    message_request: NewMessageRequest,
    background_tasks: BackgroundTasks, # Add background_tasks here
    db: AsyncIOMotorDatabase = Depends(get_mongo_client),
    sessions_collection: AsyncIOMotorCollection = Depends(get_sessions_collection)
):
    with open("debug_api.txt", "a") as f:
        f.write(f"add_message_to_session called for {session_id}\n")
    try:
        # Create a Message object
        new_message = Message(
            session_id=session_id,
            sender=message_request.sender,
            text=message_request.text,
            channel=message_request.channel,
            timestamp=datetime.utcnow()
        )
        
        # Prepare update operations
        update_operations = {
            "$push": {"messages": new_message.dict(exclude_none=True)},
            "$set": {"updated_at": datetime.utcnow()}
        }
        
        # If telegram_user_id is provided, also set it on the customer object
        if message_request.telegram_user_id:
            # We need to explicitly set the customer.telegram_user_id
            # This handles cases where the session might not have it yet
            update_operations["$set"]["customer.telegram_user_id"] = message_request.telegram_user_id
            print(f"--- Updating session {session_id} with customer.telegram_user_id: {message_request.telegram_user_id} ---")

        update_result = await sessions_collection.update_one(
            {"_id": session_id},
            update_operations
        )
        
        if update_result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID {session_id} not found")
        
        updated_session_doc = await sessions_collection.find_one({"_id": session_id})
        if updated_session_doc:
            updated_session = Session.model_validate(updated_session_doc)
            
            # Enqueue Local LLM analysis as a background task (Always run Local LLM)
            background_tasks.add_task(run_local_llm_analyze, updated_session.session_id, db, background_tasks)
            
            # --- Conditional Gemini Triggering ---
            should_trigger_gemini = False
            trigger_reason = ""

            # Condition 1: Every 5 messages
            # Count only customer and agent messages? Or all? User said "every 5 messages".
            # Let's count total messages for simplicity, or maybe just customer messages?
            # Usually "every 5 messages" implies conversation turns.
            msg_count = len(updated_session.messages)
            if msg_count > 0 and msg_count % 5 == 0:
                should_trigger_gemini = True
                trigger_reason = "message_count_5"

            # Condition 2: Sudden intent change
            # We need to compare the NEW Local LLM analysis with the OLD one.
            # But run_local_llm_analyze is a background task, so we don't have the result yet!
            # To implement this correctly, we should probably move the Gemini trigger logic INSIDE run_local_llm_analyze
            # after it completes.
            
            # However, for now, let's just trigger based on message count here, 
            # and I will move the "Intent Change" check to `run_local_llm_analyze` in the next step.
            
            # Actually, let's NOT trigger Gemini here at all. 
            # We should trigger it from `run_local_llm_analyze` after the local analysis is done.
            # That way we can check for intent change AND message count.
            
            # So I will remove the direct Gemini trigger (if any existed) or just rely on the background task.
            # Wait, the previous code didn't trigger Gemini automatically here, only Local LLM.
            # The user wants "gemini api will be triggered after meeting condition".
            # So I should add the logic to `run_local_llm_analyze`.
            
            # Broadcast the updated session to the client
            await manager.send_session_update(session_id, updated_session.model_dump(mode='json'))

            return updated_session
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated session")
            
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")



@app.post("/api/sessions/{session_id}/send", response_model=Session)
async def send_outbound_message(
    session_id: str,
    send_request: SendMessageRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_client),
    sessions_collection: AsyncIOMotorCollection = Depends(get_sessions_collection)
):
    try:
        session = await sessions_collection.find_one({"_id": session_id})
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID {session_id} not found")
        
        customer_phone = session.get("customer", {}).get("phone")
        if not customer_phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer phone not found in session")
        
        # Use the TelegramRouter to send the message
        telegram_send_result = await telegram_router.send_message(customer_phone, send_request.text)
        
        if telegram_send_result.get("status") == "error":
            # If sending fails, we might still want to record the attempt or raise an error
            print(f"Failed to send Telegram message: {telegram_send_result.get('detail')}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send message: {telegram_send_result.get('detail')}")

        # Update session with telegram_user_id if available and not set
        if "telegram_user_id" in telegram_send_result:
            tid = telegram_send_result["telegram_user_id"]
            current_tid = session.get("customer", {}).get("telegram_user_id")
            if current_tid != tid:
                print(f"--- Learning Telegram User ID {tid} for session {session_id} ---")
                await sessions_collection.update_one(
                    {"_id": session_id},
                    {"$set": {"customer.telegram_user_id": tid}}
                )

        # Create a Message object as if sent by the agent
        new_message = Message(
            session_id=session_id,
            sender="agent",
            text=send_request.text,
            channel="telegram", # Sent via Telegram
            timestamp=datetime.utcnow()
        )
        
        update_result = await sessions_collection.update_one(
            {"_id": session_id},
            {
                "$push": {"messages": new_message.dict(exclude_none=True)},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if update_result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID {session_id} not found")
        
        updated_session_doc = await sessions_collection.find_one({"_id": session_id})
        if updated_session_doc:
            session_to_broadcast = Session.model_validate(updated_session_doc)
            # Broadcast the updated session to the client
            await manager.send_session_update(session_id, session_to_broadcast.model_dump(mode='json'))
            return session_to_broadcast
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated session")
            
    except pymongo.errors.PyMongoError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")


@app.post("/api/sessions/{session_id}/trigger_gemini", response_model=GeminiAnalysis)
async def trigger_gemini_analysis(
    session_id: str,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_mongo_client),
    sessions_collection: AsyncIOMotorCollection = Depends(get_sessions_collection)
):
    # Enqueue the background task
    background_tasks.add_task(run_gemini_call, session_id, request.text, db)
    
    # Immediately fetch and return the current gemini analysis (might be empty or old)
    # The frontend will update in real-time via WebSocket once the task completes
    session_doc = await sessions_collection.find_one({"_id": session_id})
    if session_doc and session_doc.get("gemini"):
        return GeminiAnalysis.model_validate(session_doc["gemini"])
    else:
        # Return an empty GeminiAnalysis if no analysis exists yet
        return GeminiAnalysis()

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks, db: AsyncIOMotorDatabase = Depends(get_mongo_client)):
    """
    Placeholder for Telegram webhook receiver.
    This endpoint will receive incoming messages from Telegram.
    """
    payload = await request.json()
    print(f"--- Received Telegram Webhook ---")
    print(f"Payload: {payload}")
    print(f"---------------------------------")

    # TODO: Parse payload, extract sender, text.
    # For now, let's assume we extract a phone number and message text
    mock_sender_phone = payload.get("message", {}).get("from", {}).get("phone_number", "+1234567890") # Mock
    mock_message_text = payload.get("message", {}).get("text", "Default webhook message") # Mock
    
    # Find session by phone number (requires a lookup across customer.phone field)
    # This is a simplification; a real system would map Telegram chat_id to session
    sessions_collection = db["sessions"]
    session_doc = await sessions_collection.find_one({"customer.phone": mock_sender_phone})

    if session_doc:
        session_id = str(session_doc["_id"])
        # Use add_message_to_session logic
        new_message_request = NewMessageRequest(
            sender="customer",
            text=mock_message_text,
            channel="telegram"
        )
        # We need the sessions_collection for add_message_to_session
        sessions_collection_dep = db["sessions"]
        await add_message_to_session(session_id, new_message_request, background_tasks, db, sessions_collection_dep)
        print(f"--- Processed incoming Telegram message for session {session_id} ---")
    else:
        print(f"--- No session found for phone number {mock_sender_phone}. Creating a stub session. ---")
        # For now, if no session, just print. In a real scenario, you might create a new session stub.
        # This requires more advanced logic for new conversations via webhook.

    # Return 200 OK to Telegram to acknowledge receipt
    return {"status": "success", "message": "Webhook received"}
