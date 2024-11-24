import os
import re
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import Tool
from dotenv import load_dotenv, find_dotenv
import json

dotenv_path = find_dotenv("./.env")
load_dotenv(dotenv_path)

CHAT_HISTORY_FILE = "chat_history.json"
ADDON_TOOLS_FILE = "tools/addOnTools.py"  # Path to addOnTools.py

def load_recent_history():
    """Load recent chat history for context."""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            chat_history = json.load(f)
        print(f"Tool input : {chat_history[-1:]}")
        return chat_history[-1:]  # Get the last 3 interactions for context
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

def extract_and_save_python_code(input_text, output_file="./tools/addOnTools.py"):
    """
    Extract Python code from the text using regex and save it to a file.
    If no Python-specific block is found, it extracts generic code snippets.

    Args:
    - input_text (str): The text containing Python code or code snippets.
    - output_file (str): The name of the file where the extracted code will be saved.

    Returns:
    - str: The extracted Python code or None if no code is found.
    """
    # Regex for Python-specific blocks (with language hint)
    python_block_regex = re.compile(r'```python([\s\S]*?)```')

    # Fallback regex for any generic code block
    generic_code_block_regex = re.compile(r'```([\s\S]*?)```')

    # Try matching Python-specific blocks first
    match = python_block_regex.search(input_text)
    if not match:
        # Fall back to matching generic code blocks
        match = generic_code_block_regex.search(input_text)

    if match:
        python_code = match.group(1).strip()

        # Save the extracted code to a file
        try:
            with open(output_file, "w") as file:
                file.write(python_code)
            print(f"Python code successfully saved to {output_file}.")
        except IOError as e:
            print(f"Error saving to file: {e}")

        return python_code
    else:
        print("No Python code block found in the input text.")
        return None

def toolGenTool(input_text, code_gen: bool = False):
    recent_history = load_recent_history()
    context = " ".join([f"User: {item['user']} Agent: {item['agent']}" for item in recent_history])
    llm = ChatGroq(model="llama3-70b-8192", temperature=0)
    prompt = PromptTemplate(
        template="""Using the following recent history as context: {context}

Generate the complete Python scripts for each of the specified functionalities as determined by the decomposer. The solution must form a minimal, functional framework that is executable without requiring any API keys or additional costs. Ensure that the implementation can run entirely on a local environment without any dependencies that involve monetary requirements or subscriptions.

Each specific functionality should be encapsulated in a separate Python function. These functions must work together in the specified order, and the overall workflow should be orchestrated via a dedicated tool function.

Define each function and the tool using the following format:

# Define the functions
def func1(input):
    # Functionality for tool1
    return "Output from func1"

def func2(input):
    # Functionality for tool2
    return "Output from func2"

def func3(input):
    # Functionality for tool3
    return "Output from func3"

# Define the tool that calls the functions in the correct order

from langchain.agents import Tool
def run(input):
   # Enter the correct order of calling the functions along with passing the inputs
   # For eg : 
   o1 = func1(input)
   o2 = func2(o1)
   o3 = func3(o2)
   return o3

run = Tool(
    name='Run',
    func=run,
    description="To execute the code, usually to be done after Tool Gen"
)


updatedTools = [run]

Make sure the solution includes the necessary boilerplate and any required imports, ensuring the script is ready to run immediately. If any example input/output demonstration is required, include it in the response for clarity.


Keep in mind to define run as a LANGCHAIN TOOL and not a function. and define the tool EXACTLY THE SAME WAY AS MENTIONED.
also keep in mind that the description of the run tool should only describe what would happen if the person executed the code

Also clearly specify if there are any libraries to install before executing the code

DONT GENERATE CODE WHERE I WOULD NEED EXTERNAL API, BUILD A SCRAPER TO ACCOMPLISH ALL TASKS THAT WOULD REQUIRE AN API

"""

,
        input_variables=["input_text", "context"],
)
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"context": context, "input_text": input_text})

    print(f"Result : {result}")
    save_to_chat_history(input_text, result)

    # Store the python code in addOnTools.py
    extract_and_save_python_code(result)

    return result



toolGen = Tool(
    name='Tool Generator',
    func=toolGenTool,
    description="This is to be used to generate new tools"
)
