# tg_user_terminal.py
import asyncio
from telethon import TelegramClient, events, errors
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import InputPeerUser
import getpass
import sys
import os
from dotenv import load_dotenv
load_dotenv()
# ---- Configurable: Session filename base ----
SESSION_NAME = "tg_user_session"   # will create tg_user_session.session
async def main():
    print("=== Telegram user client (terminal) ===")
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    phone = "ENTER PHONE NUMBER"

    # Create client
    client = TelegramClient(SESSION_NAME, api_id=int(api_id), api_hash=api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        try:
            # send code
            await client.send_code_request(phone)
            code = input("Enter the code you received (Telegram/SMS): ").strip()
            try:
                await client.sign_in(phone=phone, code=code)
            except errors.SessionPasswordNeededError:
                # 2FA enabled - ask for password securely
                pw = getpass.getpass("Two-step password required. Enter your password: ")
                await client.sign_in(password=pw)
        except Exception as e:
            print("Sign-in failed:", type(e).__name__, e)
            await client.disconnect()
            return

    print("Signed in as", (await client.get_me()).username or (await client.get_me()).first_name)

    # Ask for contact identifier
    contact_q = "@mr_shanx"

    # Resolve contact entity
    target = None
    # 1) if starts with + treat as phone
    if contact_q.startswith('+'):
        try:
            entity = await client.get_entity(contact_q)   # phone lookup
            target = entity
        except Exception:
            target = None

    # 2) if starts with @ treat as username
    if target is None and contact_q.startswith('@'):
        try:
            entity = await client.get_entity(contact_q)
            target = entity
        except Exception:
            target = None

    # 3) fallback: search by name fragment (returns first match)
    if target is None:
        try:
            results = await client(functions.contacts.SearchRequest(
                q=contact_q, limit=10
            ))
            users = results.users
            if users:
                user = users[0]
                print(f"Found: {getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')} (id={user.id})")
                target = await client.get_entity(user)
        except Exception:
            target = None

    if target is None:
        print("Could not resolve contact. Try using exact phone (+country) or @username.")
        await client.disconnect()
        return

    # Print detailed info about the target user
    try:
        from telethon.tl.functions.users import GetFullUser
        full = await client(GetFullUser(user=target))
    except Exception:
        full = None

    try:
        entity = await client.get_entity(target)
    except Exception:
        entity = target

    print("\n=== TARGET INFO ===")
    def _g(obj, name, default=None):
        return getattr(obj, name, default)

    print(f"id: {_g(entity, 'id', 'N/A')}")
    print(f"username: {_g(entity, 'username', 'N/A')}")
    print(f"first_name: {_g(entity, 'first_name', 'N/A')}")
    print(f"last_name: {_g(entity, 'last_name', 'N/A')}")
    print(f"phone: {_g(entity, 'phone', 'N/A')}")

    # Now get message text
    text = input("Enter message to send: ").strip()
    if not text:
        print("No message entered. Exiting.")
        await client.disconnect()
        return

    try:
        sent = await client.send_message(target, text)
        print(f"Message sent (id={sent.id})")
    except errors.FloodWaitError as fwe:
        print(f"Flood wait: need to wait {fwe.seconds} seconds.")
        await client.disconnect()
        return
    except Exception as e:
        print("Failed to send:", type(e).__name__, e)
        await client.disconnect()
        return

    # Event handler: print incoming messages from this contact in terminal
    @client.on(events.NewMessage(incoming=True, from_users=target))
    async def handler(event):
        sender = await event.get_sender()
        name = (sender.first_name or "") + (" " + sender.last_name if sender.last_name else "")
        txt = event.raw_text
        print("\n--- NEW MESSAGE ---")
        print(f"From: {name} (@{sender.username if sender.username else 'no-username'})")
        print(f"Message ID: {event.message.id}")
        print(f"Text: {txt}")
        if event.message.media:
            print("[media attached: type=", type(event.message.media), "]")
        print("-------------------\n")

    async def stdin_loop():
        print("Type messages and press Enter to send. Use /quit to exit.")
        loop = asyncio.get_running_loop()
        while True:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if line == "":
                    # EOF (e.g., Ctrl+D)
                    await client.disconnect()
                    break
                msg = line.strip()
                if not msg:
                    continue
                if msg.lower() in ("/quit", "/exit"):
                    await client.disconnect()
                    break
                try:
                    await client.send_message(target, msg)
                    print("(you) -> sent")
                except Exception as e:
                    print("Failed to send:", type(e).__name__, e)
            except (asyncio.CancelledError, KeyboardInterrupt):
                break

    print("Listening for replies from target. Press Ctrl+C to quit.")
    try:
        await asyncio.gather(
            client.run_until_disconnected(),
            stdin_loop(),
        )
    finally:
        await client.disconnect()

if __name__ == "__main__":
    import sys
    from telethon import functions
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)
