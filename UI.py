import asyncio
from google import genai
import json
import os
import time
import html

import streamlit as st
from dotenv import load_dotenv
from streamlit_chat import message

from redis_facil import RedisFacil
from streamlit_autorefresh import st_autorefresh


load_dotenv()

# Rerun the app every 1000 ms
st_autorefresh(interval=1000, key="tg_autorefresh")

# Set up page config first (must be first Streamlit command)
st.set_page_config(
    page_title="chat",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)


# Initialize Redis connection
redis_facil = RedisFacil()

# Set org ID and API key
# genai.configure(api_key=os.getenv("GREMINI_API_KEY"))
api_key = os.getenv("GEMINI_API_KEY")
global client 
client = genai.Client(api_key=api_key)

def run_redis_async(coro):
    """Run a Redis async operation in a fresh event loop.
    
    Creates a new event loop for each Redis operation to avoid
    conflicts with Streamlit's event loop.
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If no loop exists, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        print(f"Redis operation failed: {e}")
        raise

# Initialise session state variables
if 'chat_sessions' not in st.session_state:
    st.session_state['chat_sessions'] = {}
if 'current_chat_id' not in st.session_state:
    st.session_state['current_chat_id'] = "default_chat"

# Initialize current chat session if it doesn't exist
if st.session_state['current_chat_id'] not in st.session_state['chat_sessions']:
    st.session_state['chat_sessions'][st.session_state['current_chat_id']] = {
        'generated': [],
        'past': [],
        'messages': [
            {"role": "user", "parts": ["You are a helpful assistant."]},
            {"role": "model", "parts": ["How can I help you today?"]}
        ],
    }

# Alias current chat session for easier access
current_chat = st.session_state['chat_sessions'][st.session_state['current_chat_id']]

# Telegram chat state (left pane)
if 'tg_messages' not in st.session_state:
    st.session_state['tg_messages'] = []

REDIS_TOPIC = "telegram_chat"
redis_facil = RedisFacil()

# Function to check for new messages
def check_new_messages(max_retries: int = 3) -> bool:
    """Check for new messages with retry logic.
    Returns True if new messages were found and processed.
    """
    for attempt in range(max_retries):
        try:
            # First check if Redis is alive
            try:
                run_redis_async(redis_facil._redis.ping())
            except:
                time.sleep(0.1)
                continue
                
            messages = run_redis_async(redis_facil.read_incoming_msgs(REDIS_TOPIC, batch_size=20))
            
            if messages:  # Only process if we got messages
                for payload in messages:
                    text = payload.get("text", "") if isinstance(payload, dict) else str(payload)
                    if not text:
                        continue
                        
                    sender_name = "Telegram"
                    if isinstance(payload, dict):
                        sender_name = payload.get("sender_name") or payload.get("sender_username") or sender_name
                        
                    # Deduplicate messages using message_id if available
                    msg_id = payload.get("message_id") if isinstance(payload, dict) else None
                    if msg_id:
                        # Skip if we've already seen this message
                        if any(m.get("message_id") == msg_id for m in st.session_state['tg_messages']):
                            continue
                            
                    st.session_state['tg_messages'].append({
                        "role": "peer",
                        "sender": sender_name,
                        "text": text,
                        "message_id": msg_id,
                        "timestamp": time.time()
                    })
                return True
            return False
            
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                print(f"Failed to check messages after {max_retries} attempts: {e}")
                return False
            time.sleep(0.5)  # Wait before retry
            continue
    return False

# Check for new messages
check_new_messages()    

# Sidebar - chat session management for Gemini chat
st.sidebar.title("Chat Controls")
st.sidebar.subheader("Chat Sessions")
chat_names = list(st.session_state['chat_sessions'].keys())
selected_chat_name = st.sidebar.selectbox("Select a chat:", chat_names, key="chat_selector_unique")

if selected_chat_name != st.session_state['current_chat_id']:
    st.session_state['current_chat_id'] = selected_chat_name
    st.rerun()

new_chat_name = st.sidebar.text_input("New chat name:", key="new_chat_input_unique")
if st.sidebar.button("Create New Chat", key="create_chat_btn_unique"):
    if new_chat_name and new_chat_name not in st.session_state['chat_sessions']:
        st.session_state['chat_sessions'][new_chat_name] = {
            'generated': [],
            'past': [],
            'messages': [
                {"role": "user", "parts": ["You are a helpful assistant."]},
                {"role": "model", "parts": ["How can I help you today?"]}
            ],
        }
        st.session_state['current_chat_id'] = new_chat_name
        st.rerun()
    elif new_chat_name:
        st.sidebar.warning("Chat name already exists!")
    else:
        st.sidebar.warning("Please enter a chat name.")


# generate a response using Gemini (right pane)
def generate_response(prompt):
    # Add user message to current chat session
    current_chat['messages'].append({"role": "user", "parts": [prompt]})

    # Initialize Gemini model
    
    # gemini_model = genai.GenerativeModel(model)

    # Prepare messages for Gemini API
    formatted_messages = []
    for msg in current_chat['messages']:
        if msg["role"] == "system":
            formatted_messages.append({"role": "user", "parts": [msg["content"]]})
        elif msg["role"] == "user":
            formatted_messages.append({"role": "user", "parts": [msg["content"]] if "content" in msg else msg["parts"]})
        elif msg["role"] == "assistant":
            formatted_messages.append({"role": "model", "parts": [msg["content"]] if "content" in msg else msg["parts"]})

    # Generate content using Gemini
    response_obj = client.models.generate_content(model="gemini-2.5-flash", contents=formatted_messages)
    response = response_obj.text

    # Add assistant response to current chat session
    current_chat['messages'].append({"role": "model", "parts": [response]})

    return response


# Main content area split into two columns
left_col, right_col = st.columns([1, 1])

with left_col:
    # Column header styled like a top bar
    st.markdown(
        "<div style='text-align:center; font-weight:600; font-size:1.1rem; "
        "padding:0.5rem 0; border-bottom:1px solid #333;'>TELEGRAM CHAT</div>",
        unsafe_allow_html=True,
    )

    chat_container = st.container()
    input_container = st.container()
    
    with chat_container:
        # Build a fixed-height, scrollable HTML box that fully wraps messages
        tg_html = [
            "<div style='height: 60vh; overflow-y: auto; padding:0.5rem 0.75rem 0.5rem 0; "
            "border: 1px solid #333; border-radius: 0.5rem;'>"
        ]
        if st.session_state['tg_messages']:
            for idx, msg_data in enumerate(st.session_state['tg_messages']):
                is_user = msg_data.get("role") == "user"
                sender_label = msg_data.get("sender", "") or ("You" if is_user else "Client")
                text = msg_data.get("text", "")
                safe_text = html.escape(text)
                safe_sender = html.escape(sender_label)
                align = "flex-end" if is_user else "flex-start"
                bg = "#1f2933" if is_user else "#111827"
                tg_html.append(
                    f"<div style='display:flex; justify-content:{align}; margin:0.25rem 0;'>"
                    f"<div style='max-width:80%; padding:0.4rem 0.6rem; border-radius:0.5rem; "
                    f"background:{bg}; font-size:0.9rem;'>"
                    f"<div style='font-size:0.75rem; color:#9ca3af; margin-bottom:0.15rem;'>{safe_sender}</div>"
                    f"<div style='color:#e5e7eb;'>{safe_text}</div>"
                    f"</div></div>"
                )
        else:
            tg_html.append(
                "<div style='color:#777; font-size:0.9rem;'>No messages yet. Start chatting below.</div>"
            )
        tg_html.append("</div>")
        st.markdown("".join(tg_html), unsafe_allow_html=True)
    
    with input_container:
        with st.form(key='telegram_msg_form', clear_on_submit=True):
            tg_input = st.text_input("type to chat to client:", key='telegram_msg_input')
            tg_send = st.form_submit_button(label='Send', key='telegram_send_btn')
        
        if tg_send and tg_input:
            try:
                # First add to outgoing Redis queue
                payload = {"text": tg_input}
                run_redis_async(redis_facil._redis.rpush(
                    redis_facil._outgoing_key(REDIS_TOPIC),
                    json.dumps(payload)
                ))
                
                # Then update UI
                st.session_state['tg_messages'].append({
                    "role": "user",
                    "sender": "You",
                    "text": tg_input,
                })
                st.rerun()
            except Exception as e:
                st.error(f"Failed to send message: {e}")

with right_col:
    # Column header styled like a top bar
    st.markdown(
        "<div style='text-align:center; font-weight:600; font-size:1.1rem; "
        "padding:0.5rem 0; border-bottom:1px solid #333;'>CONVOSPHERE</div>",
        unsafe_allow_html=True,
    )

    chat_container = st.container()
    input_container = st.container()

    with chat_container:
        # Fixed-height, scrollable history for Gemini chat inside a real box
        gm_html = [
            "<div style='height: 60vh; overflow-y: auto; padding:0.5rem 0.75rem 0.5rem 0; "
            "border: 1px solid #333; border-radius: 0.5rem;'>"
        ]
        if current_chat['generated']:
            for i in range(len(current_chat['generated'])):
                user_txt = current_chat["past"][i]
                bot_txt = current_chat["generated"][i]
                safe_user = html.escape(user_txt)
                safe_bot = html.escape(bot_txt)
                # user bubble
                gm_html.append(
                    "<div style='display:flex; justify-content:flex-end; margin:0.25rem 0;'>"
                    "<div style='max-width:80%; padding:0.4rem 0.6rem; border-radius:0.5rem; "
                    "background:#1f2933; font-size:0.9rem;'>"
                    "<div style='font-size:0.75rem; color:#9ca3af; margin-bottom:0.15rem;'>You</div>"
                    f"<div style='color:#e5e7eb;'>{safe_user}</div>"
                    "</div></div>"
                )
                # model bubble
                gm_html.append(
                    "<div style='display:flex; justify-content:flex-start; margin:0.25rem 0;'>"
                    "<div style='max-width:80%; padding:0.4rem 0.6rem; border-radius:0.5rem; "
                    "background:#111827; font-size:0.9rem;'>"
                    "<div style='font-size:0.75rem; color:#9ca3af; margin-bottom:0.15rem;'>Convosphere</div>"
                    f"<div style='color:#e5e7eb;'>{safe_bot}</div>"
                    "</div></div>"
                )
        else:
            gm_html.append(
                "<div style='color:#777; font-size:0.9rem;'>No messages yet. Start chatting below.</div>"
            )
        gm_html.append("</div>")
        st.markdown("".join(gm_html), unsafe_allow_html=True)

    with input_container:
        with st.form(key='gemini_msg_form', clear_on_submit=True):
            user_input = st.text_area("type to chat to gemini:", key='gemini_msg_input', height=100)
            submit_button = st.form_submit_button(label='Send', key='gemini_send_btn')

        if submit_button and user_input:
            output = generate_response(user_input)
            current_chat['past'].append(user_input)
            current_chat['generated'].append(output)

