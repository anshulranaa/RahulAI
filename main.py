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
        
        # Initialize base tools and models
        self.tools = [decomp, toolGen]
        
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
            memory=self.memory
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
        
    def save_chat_history(self, user_input: str, agent_response: str):
        """Save conversation turn to chat history."""
        if os.path.exists(self.CHAT_HISTORY_FILE):
            with open(self.CHAT_HISTORY_FILE, "r") as f:
                chat_history = json.load(f)
        else:
            chat_history = []
            
        chat_history.append({
            "user": user_input,
            "agent": agent_response
        })
        
        with open(self.CHAT_HISTORY_FILE, "w") as f:
            json.dump(chat_history, f, indent=4)
            
    def process_input(self, user_input: str):
        """Process user input and handle dynamic tool updates."""
        # Check if input is a special command for tool management
        if user_input.startswith("!tools"):
            return f"Current tools: {', '.join(self.get_tools())}"
            
        # Normal agent interaction
        agent_response = self.agent(user_input)
        self.save_chat_history(user_input, agent_response)
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