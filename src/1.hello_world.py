import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from utils.io import write_json

# Load environment variables from .env file
load_dotenv()
PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
OPENAI_CHAT_DEPLOY_NAME = os.getenv("OPENAI_CHAT_DEPLOY_NAME")

# Define constants
OUTPUT_DIR = ".output/1.hello_world"

# Create Azure AI Agent Service client
project = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)

# Create an agent
agent = project.agents.create_agent(
    model=OPENAI_CHAT_DEPLOY_NAME,
    name="hello-world-agent",
    instructions="You are a helpful assistant.",
)

# Create a thread
thread = project.agents.create_thread()

# Add a message to the thread
user_message = "Hello my AI agent."
project.agents.create_message(thread_id=thread.id, role="user", content=user_message)

# Process the thread with the agent (wait until the agent finishes processing)
run = project.agents.create_and_process_run(agent_id=agent.id, thread_id=thread.id)
write_json(f"{OUTPUT_DIR}/run.json", run.as_dict())

# List messages
messages = project.agents.list_messages(thread_id=thread.id)
write_json(f"{OUTPUT_DIR}/messages.json", messages.as_dict())

# Get and display a latest message from an assistant
message = messages.get_last_text_message_by_role(role="assistant")
write_json(f"{OUTPUT_DIR}/message.json", message.as_dict())
print(message.text.value)

# Delete the agent and the thread
project.agents.delete_agent(agent.id)
project.agents.delete_thread(thread.id)
