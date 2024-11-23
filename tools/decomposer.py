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

def decomposerTool(input_text, code_gen: bool = False):
    recent_history = load_recent_history()
    context = " ".join([f"User: {item['user']} Agent: {item['agent']}" for item in recent_history])
    llm = ChatGroq(model="llama3-70b-8192", temperature=0)
    prompt = PromptTemplate(
        template="""With the following recent history as context: {context}

        You are an AI expert with extensive knowledge in tool integration and workflow design. Your task is to decompose a given problem into the necessary tools and design an optimal flow for invoking these tools to solve the problem efficiently. Follow these steps:

Understand the Problem: Begin by thoroughly analyzing the task. Identify the main goal, sub-tasks, and potential challenges. Ensure clarity on what needs to be achieved.

Identify Required Tools: List all the tools or resources that can help accomplish the task. Explain why each tool is needed and how it contributes to the overall solution.

Design the Workflow: Create a detailed flowchart or step-by-step plan for invoking the tools. Specify:

The order in which the tools should be used.
The input each tool requires and the output it generates.
How the output from one tool will be used as input for another.
Error Handling and Optimization: Highlight any potential errors that may occur at each step and propose strategies to mitigate them. Suggest any optimizations to improve efficiency or accuracy.

Deliver the Solution: Present the final workflow and justify your choices. Ensure the plan is clear, concise, and actionable.
    {input_text}
    """,
        input_variables=["input_text","context"],
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"context": context, "input_text": input_text})

    save_to_chat_history(input_text, result)

    return result


decomp = Tool(
    name='Decomposer',
    func=decomposerTool,
    description="This is to be used when the user wants to breakdown their task into specific tools needed"
)
