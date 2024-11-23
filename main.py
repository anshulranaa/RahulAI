import os
import json
from typing import List, Dict
from langchain.agents import initialize_agent, Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferWindowMemory
from dotenv import load_dotenv, find_dotenv
from tools.decomposer import decomp
from tools.toolGen import toolGen
from tools.addOnTools import updatedTools

class Agent:
    def __init__(self):
        # Load environment variables
        dotenv_path = find_dotenv("../.env")
        load_dotenv(dotenv_path)
        
        self.CHAT_HISTORY_FILE = "chat_history.json"
        self.initialize_chat_history()

        self.tool_names = {}

        self.prompt = """
                    You are an intelligent, dynamic agent capable of handling tasks by invoking and executing tools. Follow these guidelines:

                    1. When given a task, determine the necessary tools to complete it.
                    2. Dynamically create, update, or use existing tools based on the task's requirements.
                    3. Always rely on the output (observation) from the tools to generate your final answer.
                    4. If a tool's output is ambiguous or incomplete, use reasoning to decide the next step or tool to use.

                    ---

                    ### Formatting:
                    - **Thought**: Clearly explain your reasoning at each step.
                    - **Action**: Specify the tool to use and its input in JSON format.
                    - **Observation**: Record the tool's output after execution.
                    - **Final Answer**: Use the observation to respond to the user's query.

                    ---

                    ### Examples:

                    **Example 1:**  
                    **User**: Add 2 and 3  
                    **Thought**: I need to use the "Add_Tool" to compute the result of 2 + 3.  
                    **Action**: { "tool": "Add_Tool", "input": { "numbers": [2, 3] } }  
                    **Observation**: 5  
                    **Final Answer**: The result of adding 2 and 3 is 5.

                    ---

                    **Example 2:**  
                    **User**: Scrape xyz.com and save its content in a file.  
                    **Thought**: This requires two steps:  
                    1. Use a scraping tool to extract the content from xyz.com.  
                    2. Use a file-writing tool to save the content to a file.  
                    **Action**: { "tool": "Scrape_Tool", "input": { "url": "xyz.com" } }  
                    **Observation**: "Website content extracted successfully."  
                    **Thought**: Now I will save this content to a file.  
                    **Action**: { "tool": "File_Write_Tool", "input": { "content": "Website content", "filename": "output.txt" } }  
                    **Observation**: "File saved successfully."  
                    **Final Answer**: The content from xyz.com has been successfully saved to output.txt.

                    ---

                    ### Rules:
                    - Do not assume results. Always verify with tools and observations.
                    - If a tool doesn't exist for the task, dynamically create one (if capable) or suggest a solution.

                    ---

                    Now, proceed with the user's input.
                    """

        
        # Initialize base tools and models
        self.tools = [decomp, toolGen] + updatedTools

        for tool in self.tools:
            print(tool)
            self.tool_names[tool.name] = tool
        
        # Initialize LLM and Chat models
        self.llm = ChatGroq(model="llama3-70b-8192", temperature=0)
        self.chat = ChatGroq(
            temperature=0,
            model="llama3-70b-8192",
        )
        
        # Initialize memory
        self.memory = ConversationBufferWindowMemory(
            memory_key='chat_history',
            k=3,
            return_messages=True
        )
        
        # Initialize agent
        self.agent = self._create_agent()
        
    def initialize_chat_history(self):
        """Create or overwrite the chat_history.json file with an empty list."""
        with open(self.CHAT_HISTORY_FILE, "w") as f:
            json.dump([], f)
            
    def _create_agent(self):
        """Create a new agent instance with current tools and memory."""
        return initialize_agent(
            agent='chat-conversational-react-description',
            tools=self.tools,
            llm=self.chat,
            verbose=True,
            max_iterations=3,
            early_stopping_method='generate',
            memory=self.memory,
            agent_prompt = self.prompt
        )
    
        
    def add_tool(self, tool: Tool):
        """Add a new tool and reinitialize the agent."""
        if tool.name not in self.tool_names:

            self.tools.extend(updatedTools)
            self.tool_names[tool.name] = tool
            # Reinitialize agent with updated tools
            self.agent = self._create_agent()
            return True
        return False
        
    def remove_tool(self, tool_name: str):
        """Remove a tool by name and reinitialize the agent."""
        if tool_name in self.tool_names:
            tool = self.tool_names[tool_name]
            self.tools.remove(tool)
            del self.tool_names[tool_name]
            # Reinitialize agent with updated tools
            self.agent = self._create_agent()
            return True
        return False
        
    def get_tools(self) -> List[str]:
        """Get list of current tool names."""
        return list(self.tool_names.keys())
        
    def save_chat_history(self, user_input: str, agent_response: dict):
        """Save conversation turn to chat history."""
        if os.path.exists(self.CHAT_HISTORY_FILE):
            with open(self.CHAT_HISTORY_FILE, "r") as f:
                chat_history = json.load(f)
        else:
            chat_history = []
            
        # Append the latest conversation
        chat_history.append({
            "user": user_input,
            "agent": agent_response
        })
        
        # Save back to file
        with open(self.CHAT_HISTORY_FILE, "w") as f:
            json.dump(chat_history, f, indent=4)

            
    def process_input(self, user_input: str):
        """Process user input and handle dynamic tool updates."""
        # Check if input is a special command for tool management
        if user_input.startswith("!tools"):
            return f"Current tools: {', '.join(self.get_tools())}"
            
        # Normal agent interaction
        agent_response = self.agent(user_input)
        
        # Extract observation and other relevant details
        thought = agent_response.get("thought", "No thought recorded")
        action = agent_response.get("action", "No action recorded")
        observation = agent_response.get("observation", "No observation recorded")
        final_answer = agent_response.get("output", "No final answer")
        
        # Save chat history with extracted details
        self.save_chat_history(user_input, {
            "thought": thought,
            "action": action,
            "observation": observation,
            "final_answer": final_answer
        })
        
        return agent_response


def main():
    agent = Agent()
    
    print("Dynamic Tool Agent initialized. Type '!tools' to see available tools.")
    print("Enter your queries or commands:")
    
    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() == 'exit':
                break
                
            response = agent.process_input(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()