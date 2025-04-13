import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ToolSet, AzureAISearchTool
from utils.io import write_json

# Load environment variables from .env file
load_dotenv()
AZURE_AI_AGENT_PROJECT_CONNECTION_STRING = os.getenv("AZURE_AI_AGENT_PROJECT_CONNECTION_STRING")
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
AI_SEARCH_INDEX_NAME = os.getenv("AI_SEARCH_INDEX_NAME")
AI_SEARCH_CONNECTION_NAME = os.getenv("AI_SEARCH_CONNECTION_NAME")

# Define constants
OUTPUT_DIR = ".output/2.rag"

# Create Azure AI Agent Service client
project = AIProjectClient.from_connection_string(
    conn_str=AZURE_AI_AGENT_PROJECT_CONNECTION_STRING,
    credential=DefaultAzureCredential(),
)

# Define tools for the agent
ai_search_connection_id = project.connections.get(connection_name=AI_SEARCH_CONNECTION_NAME).id
ai_search = AzureAISearchTool(index_connection_id=ai_search_connection_id, index_name=AI_SEARCH_INDEX_NAME)
toolset = ToolSet()
toolset.add(ai_search)

# Create an agent
agent = project.agents.create_agent(
    model=AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME,
    name="rag-agent",
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

# Process the thread with the agent (wait until the agent finishes processing)
run = project.agents.create_and_process_run(agent_id=agent.id, thread_id=thread.id)
write_json(f"{OUTPUT_DIR}/run.json", run.as_dict())

# List run steps
run_steps = project.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
write_json(f"{OUTPUT_DIR}/run_steps.json", run_steps.as_dict())
for i, run_step in enumerate(reversed(run_steps.data)):
    run_step = run_step.as_dict()
    message = f"[Step {i}] {run_step['type']}"
    step_details = run_step["step_details"]
    if step_details["type"] == "tool_calls":
        used_queries = ", ".join([f'Query: {d["azure_ai_search"]["input"]}' for d in step_details["tool_calls"] if d["type"] == "azure_ai_search"])
        message += f" ({used_queries})"
    print(message)

# List messages
messages = project.agents.list_messages(thread_id=thread.id)
write_json(f"{OUTPUT_DIR}/messages.json", messages.as_dict())

# Get and display a latest message from an assistant
message = messages.get_last_text_message_by_role(role="assistant")
write_json(f"{OUTPUT_DIR}/message.json", message.as_dict())
print("\n".join(["", "-" * 50, "Assistant Message", "-" * 50]))
print(message.text.value)

# Delete the agent and the thread
project.agents.delete_agent(agent.id)
project.agents.delete_thread(thread.id)
