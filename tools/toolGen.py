import os
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import Tool
from dotenv import load_dotenv, find_dotenv
import json



dotenv_path = find_dotenv("./.env")
load_dotenv(dotenv_path)

CHAT_HISTORY_FILE = "chat_history.json"

def load_recent_history():
    """Load recent chat history for context."""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            chat_history = json.load(f)
        return chat_history[-3:]  # Get the last 3 interactions for context
    return []

def save_to_chat_history(user_input, tool_output):
    """Save the current interaction to chat_history.json in the specified format."""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            chat_history = json.load(f)
    else:
        chat_history = []

    # Prepare the current interaction format
    interaction = {
        "user": user_input,
        "agent": {
            "input": user_input,
            "chat_history": load_recent_history(),
            "output": tool_output
        }
    }

    # Append the new interaction to the chat history
    chat_history.append(interaction)

    # Save back to the JSON file
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(chat_history, f, indent=4)

def toolGenTool(input_text, code_gen: bool = False):
    recent_history = load_recent_history()
    context = " ".join([f"User: {item['user']} Agent: {item['agent']}" for item in recent_history])
    llm = ChatGroq(model="llama3-70b-8192", temperature=0)
    prompt = PromptTemplate(
        template="""With the following recent history as context: {context}

        Understand the Problem:

Analyze the task to determine the required functionality.
Identify the tools needed, the logic for each tool, and their interdependencies.
Generate Tool Code:

Write Python code for each tool as a modular function.
Include necessary imports and environmental configurations.
Adhere to best practices, ensuring clean, readable, and efficient code.
Define the Workflow:

Outline the sequence in which the tools will be invoked.
Handle input and output flow between tools.
Store the Code:

Save the generated code in a separate .py file.
Ensure the file is self-contained, including all imports and helper functions.
Example Format : 

import os
import json
from langchain.agents import initialize_agent

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import Tool
from dotenv import load_dotenv, find_dotenv
from tools.decomposer import decomp
from tools.toolGen import toolGen


dotenv_path = find_dotenv("../.env")
load_dotenv(dotenv_path)

CHAT_HISTORY_FILE = "chat_history.json"

# Ensure chat_history.json is reset at the start of each session
def initialize_chat_history():
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump([], f)

initialize_chat_history()  # Initialize the file at the start


def tool(input_text):
    #Enter functionality of tool as per specifications

toolName = Tool(
    name='Decomposer',
    func=decomposerTool,
    description="This is to be used when the user wants to breakdown their task into specific tools needed"
)

    {input_text}
    """,
        input_variables=["input_text","context"],
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"context": context, "input_text": input_text})

    save_to_chat_history(input_text, result)

    return result


toolGen = Tool(
    name='Tool Generator',
    func=toolGenTool,
    description="This is to be used to generate new tools"
)


# TODO : Need to parse the python code given by the LLM and store them in addOnTools.py