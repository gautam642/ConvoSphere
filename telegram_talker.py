import asyncio
import getpass
import os
import sys

from dotenv import load_dotenv
from telethon import TelegramClient, events, errors, functions
# from telethon.tl.functions.users import GetFullUser

from redis_facil import RedisFacil


load_dotenv()

# ---- Configurable: Session filename base ----
SESSION_NAME = "tg_user_session"   # will create tg_user_session.session

# Topic used for Redis bridge; UI should use the same topic name.
REDIS_TOPIC = "telegram_chat"


async def ensure_authorized(client: TelegramClient, phone: str) -> None:
    if await client.is_user_authorized():
        return

    try:
        await client.send_code_request(phone)
        code = input("Enter the code you received (Telegram/SMS): ").strip()
        try:
            await client.sign_in(phone=phone, code=code)
        except errors.SessionPasswordNeededError:
            pw = getpass.getpass("Two-step password required. Enter your password: ")
            await client.sign_in(password=pw)
    except Exception as e:
        print("Sign-in failed:", type(e).__name__, e)
        await client.disconnect()
        raise


async def resolve_contact(client: TelegramClient, contact_q: str):
    """Resolve a contact by phone, @username, or name fragment."""
    target = None

    if contact_q.startswith('+'):
        try:
            entity = await client.get_entity(contact_q)
            target = entity
        except Exception:
            target = None

    if target is None and contact_q.startswith('@'):
        try:
            entity = await client.get_entity(contact_q)
            target = entity
        except Exception:
            target = None

    if target is None:
        try:
            results = await client(functions.contacts.SearchRequest(q=contact_q, limit=10))
            users = results.users
            if users:
                user = users[0]
                print(f"Found: {getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')} (id={user.id})")
                target = await client.get_entity(user)
        except Exception:
            target = None

    return target


def print_target_info(entity, full):
    print("\n=== TARGET INFO ===")

    def _g(obj, name, default=None):
        return getattr(obj, name, default)

    print(f"id: {_g(entity, 'id', 'N/A')}")
    print(f"username: {_g(entity, 'username', 'N/A')}")
    print(f"first_name: {_g(entity, 'first_name', 'N/A')}")
    print(f"last_name: {_g(entity, 'last_name', 'N/A')}")
    print(f"phone: {_g(entity, 'phone', 'N/A')}")


async def register_incoming_handler(client: TelegramClient, target, redis_facil: RedisFacil, topic: str) -> None:
    @client.on(events.NewMessage(incoming=True, from_users=target))
    async def handler(event):  # type: ignore[unused-variable]
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

        payload = {
            "sender_name": name,
            "sender_username": sender.username,
            "message_id": event.message.id,
            "text": txt,
            "has_media": bool(event.message.media),
            "date": event.message.date.isoformat() if event.message.date else None,
        }
        await redis_facil.send_recvd_msg_to_ui(topic, payload)


async def outbound_loop(client: TelegramClient, target, redis_facil: RedisFacil, topic: str) -> None:
    print("Outbound loop started. Waiting for UI messages in Redis...")
    while True:
        try:
            msg = await redis_facil.send_user_entered_msg_to_client(topic, timeout=0)
            if msg is None:
                continue
            text = msg.get("text") if isinstance(msg, dict) else str(msg)
            if not text:
                continue
            try:
                sent = await client.send_message(target, text)
                print(f"(UI -> Telegram) sent id={sent.id}")
            except errors.FloodWaitError as fwe:
                print(f"Flood wait: need to wait {fwe.seconds} seconds.")
            except Exception as e:
                print("Failed to send:", type(e).__name__, e)
        except (asyncio.CancelledError, KeyboardInterrupt):
            break


async def main() -> None:
    print("=== Telegram user client (Redis bridge) ===")
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    phone = os.getenv("PHONE_NUMBER", "ENTER PHONE NUMBER")
    contact_q = os.getenv("TG_CONTACT", "")

    if not api_id or not api_hash:
        print("API_ID and API_HASH must be set in environment or .env file")
        return

    client = TelegramClient(SESSION_NAME, api_id=int(api_id), api_hash=api_hash)
    redis_facil = RedisFacil()

    try:
        await client.connect()
        await ensure_authorized(client, phone)

        me = await client.get_me()
        print("Signed in as", me.username or me.first_name)

        target = await resolve_contact(client, contact_q)
        if target is None:
            print("Could not resolve contact. Try using exact phone (+country) or @username.")
            return

        # try:
        #     full = await client(GetFullUser(user=target))
        # except Exception:
        #     full = None
        full = await client.get_entity(contact_q)

        try:
            entity = await client.get_entity(target)
        except Exception:
            entity = target

        print_target_info(entity, full)

        await register_incoming_handler(client, target, redis_facil, REDIS_TOPIC)

        print("Listening for replies from target and bridging via Redis. Press Ctrl+C to quit.")
        await asyncio.gather(
            client.run_until_disconnected(),
            outbound_loop(client, target, redis_facil, REDIS_TOPIC),
        )
    finally:
        await client.disconnect()
        await redis_facil.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)

