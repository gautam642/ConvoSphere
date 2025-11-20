import asyncio
from google import genai
import json
import os
import time
import html
from pathlib import Path

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


CHAT_DIR = Path("chats")
CHAT_DIR.mkdir(exist_ok=True)

# Initialize Redis connection
redis_facil = RedisFacil()

# Global layout tweak: reduce top padding of main container
st.markdown(
    "<style>.block-container {padding-top: 0.75rem;}</style>",
    unsafe_allow_html=True,
)

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

def get_chat_file_path(chat_id: str) -> Path:
    return CHAT_DIR / f"{chat_id}.json"


def load_existing_chats() -> dict:
    chats: dict[str, dict] = {}
    if not CHAT_DIR.exists():
        return chats
    for file in CHAT_DIR.glob("*.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            chat_id = file.stem
            # Ensure required keys
            data.setdefault("generated", [])
            data.setdefault("past", [])
            data.setdefault("messages", [])
            chats[chat_id] = data
        except Exception:
            continue
    return chats


def save_chat(chat_id: str) -> None:
    if 'chat_sessions' not in st.session_state:
        return
    data = st.session_state['chat_sessions'].get(chat_id)
    if not data:
        return
    path = get_chat_file_path(chat_id)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# Initialise session state variables
if 'chat_sessions' not in st.session_state:
    st.session_state['chat_sessions'] = load_existing_chats()
if 'current_chat_id' not in st.session_state:
    st.session_state['current_chat_id'] = ""

# Client/session metadata
if 'client_phone' not in st.session_state:
    st.session_state['client_phone'] = ""
if 'client_name' not in st.session_state:
    st.session_state['client_name'] = ""
if 'client_details' not in st.session_state:
    st.session_state['client_details'] = ""


def ensure_current_chat() -> None:
    if not st.session_state['current_chat_id']:
        # When no chat selected, start a new one based on client info
        ts = time.strftime("%Y%m%d_%H%M%S")
        base = st.session_state.get('client_name') or "client"
        chat_id = f"{base}_start_{ts}"
        st.session_state['current_chat_id'] = chat_id
        st.session_state['chat_sessions'][chat_id] = {
            'metadata': {
                'client_phone': st.session_state['client_phone'],
                'client_name': st.session_state['client_name'],
                'client_details': st.session_state['client_details'],
                'start_timestamp': ts,
            },
            'generated': [],
            'past': [],
            'messages': [],
        }
        save_chat(chat_id)


# Startup prompt for client info (shown once)
if not st.session_state['client_name']:
    st.sidebar.markdown("### Session Setup")
    with st.sidebar.form(key="client_info_form"):
        phone = st.text_input("phone no.:", value=st.session_state['client_phone'])
        name = st.text_input("name of client:", value=st.session_state['client_name'])
        details = st.text_area("client details aware of:", value=st.session_state['client_details'], height=80)
        ok = st.form_submit_button("Start Chat")
    if not ok:
        st.stop()
    st.session_state['client_phone'] = phone.strip()
    st.session_state['client_name'] = name.strip() or "client"
    st.session_state['client_details'] = details.strip()

# Ensure there is a current chat (new one by default)
ensure_current_chat()

# Alias current chat session for easier access
current_chat = st.session_state['chat_sessions'][st.session_state['current_chat_id']]

# Telegram chat state (left pane)
if 'tg_messages' not in st.session_state:
    st.session_state['tg_messages'] = []

REDIS_TOPIC = "telegram_chat"

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
                            
                    ts_msg = time.time()
                    st.session_state['tg_messages'].append({
                        "role": "peer",
                        "sender": sender_name,
                        "text": text,
                        "message_id": msg_id,
                        "timestamp": ts_msg,
                    })
                    # Also log to persistent chat history
                    current_chat['messages'].append({
                        "source": "telegram_client",
                        "direction": "incoming",
                        "text": text,
                        "sender": sender_name,
                        "message_id": msg_id,
                        "timestamp": ts_msg,
                    })
                save_chat(st.session_state['current_chat_id'])
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

# Sidebar - chat session management for chats stored on disk
st.sidebar.title("Chat Controls")
st.sidebar.subheader("Chat Sessions")
chat_names = list(st.session_state['chat_sessions'].keys())
if not chat_names:
    chat_names = [st.session_state['current_chat_id']]
selected_chat_name = st.sidebar.selectbox(
    "Select a chat:",
    chat_names,
    index=chat_names.index(st.session_state['current_chat_id']),
    key="chat_selector_unique",
)

if selected_chat_name != st.session_state['current_chat_id']:
    st.session_state['current_chat_id'] = selected_chat_name
    current_chat = st.session_state['chat_sessions'][selected_chat_name]

# Start New Chat: reset client info so the 3-field setup form appears again
if st.sidebar.button("Start New Chat", key="create_chat_btn_unique"):
    st.session_state['client_phone'] = ""
    st.session_state['client_name'] = ""
    st.session_state['client_details'] = ""
    st.session_state['current_chat_id'] = ""
    # st.experimental_rerun()


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

    # Persist updated chat
    save_chat(st.session_state['current_chat_id'])

    return response


# Main content area split into two columns
left_col, right_col = st.columns([1, 1])

with left_col:
    # Column header styled like a top bar (reduced top margin)
    client_title = st.session_state.get('client_name') or "TELEGRAM CHAT"
    st.markdown(
        f"<div style='margin-top:0.5rem; text-align:center; font-weight:600; font-size:1.05rem; "
        f"padding:0.25rem 0; border-bottom:1px solid #333;'>{html.escape(client_title)} - TELEGRAM CHAT</div>",
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
                # Log to current chat messages for persistence
                current_chat['messages'].append({
                    "source": "telegram_ui",
                    "direction": "outgoing",
                    "text": tg_input,
                    "timestamp": time.time(),
                })
                save_chat(st.session_state['current_chat_id'])
                st.rerun()
            except Exception as e:
                st.error(f"Failed to send message: {e}")

with right_col:
    # Column header styled like a top bar (reduced top margin)
    client_title = st.session_state.get('client_name') or "CONVOSPHERE"
    st.markdown(
        f"<div style='margin-top:0.5rem; text-align:center; font-weight:600; font-size:1.05rem; "
        f"padding:0.25rem 0; border-bottom:1px solid #333;'>{html.escape(client_title)} - CONVOSPHERE</div>",
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
            # Log user + model messages in metadata log for JSON persistence
            current_chat['messages'].append({
                "source": "convosphere_ui",
                "direction": "outgoing",
                "text": user_input,
                "timestamp": time.time(),
            })
            current_chat['messages'].append({
                "source": "convosphere_model",
                "direction": "incoming",
                "text": output,
                "timestamp": time.time(),
            })
            save_chat(st.session_state['current_chat_id'])

