from flask import Flask, Response, request
import os
import json
import base64
import logging
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ToolSet, AzureAISearchTool
from utils.chat_manager import InMemoryChatManager, AgentChat

# Load environment variables from .env file
load_dotenv()
AZURE_AI_AGENT_PROJECT_CONNECTION_STRING = os.getenv("AZURE_AI_AGENT_PROJECT_CONNECTION_STRING")
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
AI_SEARCH_INDEX_NAME = os.getenv("AI_SEARCH_INDEX_NAME")
AI_SEARCH_CONNECTION_NAME = os.getenv("AI_SEARCH_CONNECTION_NAME")

# Settings about Azure AI Agent Service (instructions and toolset)
project = AIProjectClient.from_connection_string(
    conn_str=AZURE_AI_AGENT_PROJECT_CONNECTION_STRING,
    credential=DefaultAzureCredential(),
)
instructions = """
- Upon receiving a query from the user, first classify the query into one of the following categories and then plan the task accordingly.
  - No Retrieval: For simple queries that do not require a search, generate a direct response using the pre-existing knowledge of the LLM.
  - Single-Step Retrieval: For relatively simple queries that require the latest or specialized information, handle them with a single search process.
  - Multi-Step Retrieval: For complex queries, execute a multi-step search process and iteratively refine the information.
- For questions related to Azure AI Search, search the connected Azure AI Search index for relevant documents and provide answers based on those documents.
- After performing the search and generating the response, reflect on whether the user's query has been adequately addressed. If not, conduct additional information searches and revise the response accordingly.
"""
toolset = ToolSet()
ai_search_connection_id = project.connections.get(connection_name=AI_SEARCH_CONNECTION_NAME).id
ai_search = AzureAISearchTool(index_connection_id=ai_search_connection_id, index_name=AI_SEARCH_INDEX_NAME)
toolset.add(ai_search)

# Create object to manage chat sessions
chat_manager = InMemoryChatManager()

# Logging settings
logger = logging.getLogger(__name__)

# Flask app settings
app = Flask(__name__)


# Static file serving settings
@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)


@app.route("/api/chat", methods=["GET"])
def list_chats_api():
    """
    List all chat sessions for the logged-in user.
    """
    # Get information about the logged-in user
    user_id, _ = get_user_info()

    # Retrieve all chat sessions for the user
    chats = chat_manager.list_chats(user_id)

    # Convert chat sessions to a list of dictionaries for JSON serialization
    chats = [
        {
            "id": chat.chat_id,
            "title": chat.chat_title,
            "messages": chat.messages,
        }
        for chat in chats
    ]

    # Return the list of chat sessions as a JSON response
    return {"chats": chats}, 200


# Chat Web API
@app.route("/api/chat", methods=["POST"])
def create_chat_api():
    """
    Create a new chat session and return the chat ID.
    """

    # Get information about the logged-in user
    user_id, _ = get_user_info()

    # Get chat title from the request body
    chat_title = request.json.get("title", "")
    if not chat_title:
        return "Bad Request", 400

    # Create a new chat session and get the chat ID
    chat_id = str(uuid4())

    # Create Agent and Thread in Azure AI Agent Service
    agent = project.agents.create_agent(
        model=AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME,
        name=f'agent{datetime.now().strftime("%Y%m%d%H%M%S")}',
        instructions=instructions,
        toolset=toolset,
    )
    thread = project.agents.create_thread()

    # Create a new chat session
    chat = AgentChat(
        chat_id=chat_id,
        chat_title=chat_title,
        user_id=user_id,
        agent_id=agent.id,
        thread_id=thread.id,
        messages=[{"role": "assistant", "content": "Hello! How can I assist you today?"}],  # For displaying in the UI
    )

    # Store the chat session
    chat_manager.set_chat(chat_id, chat)

    # Return the chat ID as a JSON response
    return {"id": chat.chat_id, "title": chat.chat_title, "messages": chat.messages}, 200


@app.route("/api/chat/<chat_id>", methods=["DELETE"])
def delete_chat_api(chat_id: str):
    """
    Delete a chat session by its ID.
    """
    # Get information about the logged-in user
    user_id, _ = get_user_info()

    # Retrieve the chat session
    chat = chat_manager.get_chat(chat_id)
    if chat is None:
        return "Not Found", 404

    # Check if the user ID matches
    if chat.user_id != user_id:
        return "Forbidden", 403

    # Delete the chat session
    project.agents.delete_agent(chat.agent_id)
    project.agents.delete_thread(chat.thread_id)
    chat_manager.delete_chat(chat_id)

    return "", 204


@app.route("/api/chat/<chat_id>/message", methods=["POST"])
def add_message(chat_id: str):
    """
    Add a message to the chat session and stream the response from the agent.
    """

    # Get message from the request body
    message = request.json.get("message", "")
    if not message:
        return "Bad Request", 400

    # Get information about the logged-in user
    user_id, _ = get_user_info()

    # Retrieve the chat session
    chat = chat_manager.get_chat(chat_id)
    if chat is None:
        return "Not Found", 404

    # Check if the user ID matches
    if chat.user_id != user_id:
        return "Forbidden", 403

    # Add the message to the thread
    project.agents.create_message(thread_id=chat.thread_id, role="user", content=message)

    # Make the agent process messages in the thread
    stream = project.agents.create_stream(thread_id=chat.thread_id, agent_id=chat.agent_id)

    # Add the message to the chat session
    chat.messages.append({"role": "user", "content": message})

    # Response streaming from Azure AI Agent Service
    return Response(to_stream_resp(stream, chat), mimetype="text/event-stream")


def to_stream_resp(stream, chat):
    """
    Stream the response from the agent and update the chat session
    """

    # Response streaming from Azure AI Agent Service
    content = ""
    for event_type, data, func_rt in stream.event_handler:
        if event_type == "done":
            break
        resp = {"eventType": event_type}
        data = data.as_dict()
        match event_type:
            case "thread.message.delta":
                resp["delta"] = data["delta"]["content"][0]["text"]["value"]
                content += resp["delta"]
            case "thread.message.completed":
                resp["content"] = data["content"][0]["text"]
        yield json.dumps(resp)

    # Update the chat session with the final message
    chat.messages.append({"role": "assistant", "content": content})
    chat_manager.set_chat(chat.chat_id, chat)


def get_user_info() -> tuple[str, str]:
    """
    Retrieve information of the logged-in user

    Returns:
        tuple[str, str]: ID and name of the logged-in user
    """

    # Get the principal information related to Entra authentication provided in the header
    # Reference: http://schemas.microsoft.com/identity/claims/objectidentifier
    principal = request.headers.get("X-Ms-Client-Principal", "")

    # Define user ID and user name when the principal is not set
    user_id = "00000000-0000-0000-0000-000000000000"
    user_name = ""

    if principal:

        # Base64 decode the principal
        principal = base64.b64decode(principal).decode("utf-8")
        principal = json.loads(principal)

        # Define a function to get the value of a specific key from the principal
        def get_princival_value(key, default):
            claims = [c["val"] for c in principal["claims"] if c["typ"] == key]
            return claims[0] if claims else default

        # Get the user ID and user name
        user_id = get_princival_value("http://schemas.microsoft.com/identity/claims/objectidentifier", "00000000-0000-0000-0000-000000000000")
        user_name = get_princival_value("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress", "unknown")

    return (user_id, user_name)


if __name__ == "__main__":
    app.run()
