import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ToolSet, AzureAISearchTool
from utils.io import write_json

# Load environment variables from .env file
load_dotenv()
PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
OPENAI_CHAT_DEPLOY_NAME = os.getenv("OPENAI_CHAT_DEPLOY_NAME")
AI_SEARCH_INDEX_NAME = os.getenv("AI_SEARCH_INDEX_NAME")
AI_SEARCH_CONNECTION_NAME = os.getenv("AI_SEARCH_CONNECTION_NAME")

# Define constants
OUTPUT_DIR = ".output/4.streaming"

# Create Azure AI Agent Service client
project = AIProjectClient.from_connection_string(
    conn_str=PROJECT_CONNECTION_STRING,
    credential=DefaultAzureCredential(),
)

# Define tools for the agent
ai_search_connection_id = project.connections.get(connection_name=AI_SEARCH_CONNECTION_NAME).id
ai_search = AzureAISearchTool(index_connection_id=ai_search_connection_id, index_name=AI_SEARCH_INDEX_NAME)
toolset = ToolSet()
toolset.add(ai_search)

# Create an agent
agent = project.agents.create_agent(
    model=OPENAI_CHAT_DEPLOY_NAME,
    name="streaming-agent",
    instructions="""
    - Please respond to user inquiries.
    - For questions related to Azure AI Search, search the connected Azure AI Search index for relevant documents and provide answers based on those documents.
    """,
    toolset=toolset,
)

# Create a thread
thread = project.agents.create_thread()

# Add a message to the thread
user_message = "Please tell me about the Scoring Profile feature of Azure AI Search."
project.agents.create_message(thread_id=thread.id, role="user", content=user_message)

# Process the thread with the agent (receive messages as they are generated)
stream = project.agents.create_stream(thread_id=thread.id, agent_id=agent.id)

# Display the messages as they are generated
event_types = []
stream_events = []
for event_type, data, func_rt in stream.event_handler:
    # Show streaming responses
    if event_type == "thread.message.delta":
        for c in data.delta.content:
            print(c.text.value, end="")
    # Show annotations in the final message
    elif event_type == "thread.message.completed":
        for c in data.content:
            print(c.text.annotations)
    event_types.append(event_type)
    stream_events.append({"event_type": event_type, "data": data.as_dict() if type(data) is not str else None})
write_json(f"{OUTPUT_DIR}/event_types.json", event_types)
write_json(f"{OUTPUT_DIR}/stream_events.json", stream_events)

# Delete the agent and the thread
project.agents.delete_agent(agent.id)
project.agents.delete_thread(thread.id)
