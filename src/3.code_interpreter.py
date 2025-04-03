import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ToolSet, CodeInterpreterTool, FilePurpose, MessageAttachment
from utils.io import write_json

# Load environment variables from .env file
load_dotenv()
PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
OPENAI_CHAT_DEPLOY_NAME = os.getenv("OPENAI_CHAT_DEPLOY_NAME")

# Define constants
OUTPUT_DIR = ".output/3.code_interpreter"

# Create Azure AI Agent Service client
project = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)

# Define tools for the agent
code_interpreter = CodeInterpreterTool()
toolset = ToolSet()
toolset.add(code_interpreter)

# Create an agent
agent = project.agents.create_agent(
    model=OPENAI_CHAT_DEPLOY_NAME,
    name="rag-agent",
    instructions="""
    - Please respond to user inquiries.
    - Please use the Code Interpreter to handle the processing of user-uploaded files, perform numerical calculations, and generate graphs.
    """,
    toolset=toolset,
)

# Create a thread
thread = project.agents.create_thread()

# Upload a file to the AI project
file = project.agents.upload_file_and_poll(file_path="materials/sample.csv", purpose=FilePurpose.AGENTS)
attachment = MessageAttachment(file_id=file.id, tools=CodeInterpreterTool().definitions)

# Add a message to the thread
user_message = """
The uploaded file is a CSV file that represents the vector sizes of a specific search document when compressed using various “vector compression methods,” “dimensions,” and “data type bit sizes” of Azure AI Search.
From this file, please create a horizontal bar graph to make it easier to understand the vector sizes for each method.
"""
project.agents.create_message(thread_id=thread.id, role="user", content=user_message, attachments=[attachment])

# Process the thread with the agent (wait until the agent finishes processing)
run = project.agents.create_and_process_run(agent_id=agent.id, thread_id=thread.id)
write_json(f"{OUTPUT_DIR}/run.json", run.as_dict())

# List run steps
run_steps = project.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
write_json(f"{OUTPUT_DIR}/run_steps.json", run_steps.as_dict())
for i, run_step in enumerate(reversed(run_steps.data)):
    print(f"[Step {i}] {run_step.type.value}")

# List messages
messages = project.agents.list_messages(thread_id=thread.id)
write_json(f"{OUTPUT_DIR}/messages.json", messages.as_dict())

# Get and display a latest message from an assistant
message = messages.get_last_text_message_by_role(role="assistant")
write_json(f"{OUTPUT_DIR}/message.json", message.as_dict())
print("\n".join(["", "-" * 50, "Assistant Message", "-" * 50]))
print(message.text.value)

# Output generated images
for image_content in messages.image_contents:
    project.agents.save_file(
        file_id=image_content.image_file.file_id,
        target_dir=OUTPUT_DIR,
        file_name=f"{os.path.basename(image_content.image_file.file_id)}.png",
    )

# Delete the agent, the thread, the file
project.agents.delete_agent(agent.id)
project.agents.delete_thread(thread.id)
project.agents.delete_file(file.id)
