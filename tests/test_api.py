import pytest
from httpx import AsyncClient
from api.main import app
from db.database import get_mongo_client, get_redis_client # Import to use fixtures
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as aioredis # For async Redis client
import asyncio

# --- Fixtures for mocking database connections ---
@pytest.fixture(name="mongo_client")
async def mongo_client_fixture():
    # Use a test database
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db_name = "convosphere_test"
    yield client[db_name]
    # Clean up test database
    await client.drop_database(db_name)
    client.close()

@pytest.fixture(name="redis_client")
async def redis_client_fixture():
    # Use a separate Redis DB for testing
    client = aioredis.Redis(host="localhost", port=6379, db=1, decode_responses=True)
    yield client
    await client.flushdb() # Clear test data
    await client.close()

# Override dependencies for testing
async def override_get_mongo_client(mongo_client):
    yield mongo_client

async def override_get_redis_client(redis_client):
    yield redis_client

app.dependency_overrides[get_mongo_client] = override_get_mongo_client
app.dependency_overrides[get_redis_client] = override_get_redis_client


@pytest.fixture(name="client")
async def client_fixture():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# --- Tests ---
@pytest.mark.asyncio
async def test_create_session(client: AsyncClient, mongo_client: AsyncIOMotorClient):
    # Ensure collection is empty before test
    await mongo_client.get_collection("sessions").drop()

    session_data = {
        "name": "Test Customer",
        "phone": "+1234567890",
        "context": "Interested in AI solutions",
        "goal": "Sell AI product",
        "owner_id": "test_agent_001"
    }
    response = await client.post("/api/sessions", json=session_data)

    assert response.status_code == 201
    created_session = response.json()
    assert "session_id" in created_session
    assert created_session["customer"]["name"] == session_data["name"]
    assert created_session["owner"] == session_data["owner_id"]
    assert created_session["status"] == "initialized"

    # Verify session is in the database
    db_session = await mongo_client.get_collection("sessions").find_one({"_id": created_session["session_id"]})
    assert db_session is not None
    assert db_session["customer"]["name"] == session_data["name"]

@pytest.mark.asyncio
async def test_get_session(client: AsyncClient, mongo_client: AsyncIOMotorClient):
    # First, create a session directly in DB
    test_session_id = "test_session_123"
    await mongo_client.get_collection("sessions").insert_one({
        "_id": test_session_id,
        "customer": {"name": "Existing Customer", "phone": "+1112223333", "context": "None", "goal": "None"},
        "owner": "test_agent",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "messages": [], "alerts": [], "osint": {}, "local_llm": {}, "gemini": {}
    })

    response = await client.get(f"/api/sessions/{test_session_id}")

    assert response.status_code == 200
    session = response.json()
    assert session["session_id"] == test_session_id
    assert session["customer"]["name"] == "Existing Customer"

@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient):
    response = await client.get("/api/sessions/non_existent_id")
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_add_message_to_session(client: AsyncClient, mongo_client: AsyncIOMotorClient):
    test_session_id = "test_session_msg"
    await mongo_client.get_collection("sessions").insert_one({
        "_id": test_session_id,
        "customer": {"name": "Message Customer", "phone": "+1112224444", "context": "None", "goal": "None"},
        "owner": "test_agent",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "messages": [], "alerts": [], "osint": {}, "local_llm": {}, "gemini": {}
    })

    message_data = {
        "sender": "customer",
        "text": "Hello, I am interested.",
        "channel": "telegram"
    }
    response = await client.post(f"/api/sessions/{test_session_id}/messages", json=message_data)

    assert response.status_code == 200
    updated_session = response.json()
    assert len(updated_session["messages"]) == 1
    assert updated_session["messages"][0]["text"] == message_data["text"]

    # Verify in DB
    db_session = await mongo_client.get_collection("sessions").find_one({"_id": test_session_id})
    assert len(db_session["messages"]) == 1
    assert db_session["messages"][0]["text"] == message_data["text"]

@pytest.mark.asyncio
async def test_send_outbound_message(client: AsyncClient, mongo_client: AsyncIOMotorClient):
    test_session_id = "test_session_send"
    await mongo_client.get_collection("sessions").insert_one({
        "_id": test_session_id,
        "customer": {"name": "Send Customer", "phone": "+19876543210", "context": "None", "goal": "None"},
        "owner": "test_agent",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "messages": [], "alerts": [], "osint": {}, "local_llm": {}, "gemini": {}
    })

    send_data = {
        "text": "Your requested information."
    }
    response = await client.post(f"/api/sessions/{test_session_id}/send", json=send_data)

    assert response.status_code == 200
    updated_session = response.json()
    assert len(updated_session["messages"]) == 1
    assert updated_session["messages"][0]["text"] == send_data["text"]
    assert updated_session["messages"][0]["sender"] == "agent"
    assert updated_session["messages"][0]["channel"] == "telegram"

    # Verify in DB
    db_session = await mongo_client.get_collection("sessions").find_one({"_id": test_session_id})
    assert len(db_session["messages"]) == 1
    assert db_session["messages"][0]["text"] == send_data["text"]
