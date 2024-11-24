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

        self.prompt = """
You are an intelligent, dynamic agent called RAHUL. You are capable of handling tasks by invoking and executing tools. Follow these guidelines:

---

### Guidelines:
1. **Task Analysis**: When given a task, first invoke the **Breakdown tool** to decompose the task into logical subtasks, including inputs, outputs, and processing steps.
2. **Tool Generation and Usage**:
   - After obtaining the task breakdown, invoke the **ToolGen tool** to create the necessary tools for the subtasks.
   - Dynamically use or update the tools as required for the task's execution.
   - Execute each tool individually, ensuring the output from one step informs the next.
3. **Observation-Driven Execution**:
   - Always rely on the tool's output (observation) to proceed to the next step or generate the final answer.
   - If a tool's output is ambiguous or incomplete, use reasoning to decide the next step or tool to invoke.

---

### Formatting:
- **Thought**: Clearly explain your reasoning at each step.
- **Action**: Specify the tool to use and its input in JSON format.
- **Observation**: Record the tool's output after execution.
- **Final Answer**: Use the observation(s) to provide a clear and complete response to the user's query.

---

### Examples:

**Example 1:**  
**User**: Add 2 and 3  
**Thought**: I need to break this task into subtasks first.  
**Action**: { "tool": "Breakdown", "input": { "task": "Add 2 and 3" } }  
**Observation**: { "steps": [ { "tool": "Add_Tool", "input": { "numbers": [2, 3] }, "output": "5" } ] }  
**Thought**: Based on the breakdown, I need to use the Add_Tool.  
**Action**: { "tool": "Add_Tool", "input": { "numbers": [2, 3] } }  
**Observation**: 5  
**Final Answer**: The result of adding 2 and 3 is 5.

---

**Example 2:**  
**User**: Scrape xyz.com and save its content in a file.  
**Thought**: I need to break this task into subtasks first.  
**Action**: { "tool": "Breakdown", "input": { "task": "Scrape xyz.com and save its content in a file" } }  
**Observation**: { "steps": [ 
  { "tool": "Scrape_Tool", "input": { "url": "xyz.com" }, "output": "Website content" },
  { "tool": "File_Write_Tool", "input": { "content": "Website content", "filename": "output.txt" }, "output": "File saved successfully" } 
] }  
**Thought**: I will invoke ToolGen to generate these tools first.  
**Action**: { "tool": "ToolGen", "input": { "tools": ["Scrape_Tool", "File_Write_Tool"] } }  
**Observation**: Tools generated successfully.  
**Thought**: Now, I can execute the tasks in order.  
**Action**: { "tool": "Scrape_Tool", "input": { "url": "xyz.com" } }  
**Observation**: "Website content extracted successfully."  
**Thought**: Next, I will save this content to a file.  
**Action**: { "tool": "File_Write_Tool", "input": { "content": "Website content", "filename": "output.txt" } }  
**Observation**: "File saved successfully."  
**Final Answer**: The content from xyz.com has been successfully saved to output.txt.

---

### Rules:
1. **Mandatory Task Breakdown**:
   - Always invoke the **Breakdown tool** first when a new task is presented.
2. **Dynamic Tool Generation**:
   - After the breakdown, invoke the **ToolGen tool** to generate any required tools not already available.
3. **Step-by-Step Execution**:
   - Execute each tool independently, following the breakdown's logical sequence.
   - Always use the observation from one step to inform the next.
4. **Error Handling**:
   - If any tool or step fails, revisit the breakdown or tool generation process to resolve the issue.

---

Now, proceed with the user's input.
Keep in mind when the user presents with a task. The first tool to be executed should be the DECOMPOSER TOOL and after the TOOLGEN tool has been called , it is to check if any libraries are needed to be installed. Keep in mind just to pass the library names to be installed to the INSTALL_LIBRARIES FUNCTION, after that it is to invoke the RUN tool.
                    """

        
        # Initialize base tools and models
        self.tools = [decomp, toolGen] + updatedTools

        for tool in self.tools:
            print(tool)        
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
        self.agent = self._create_agent()
        return True
        
        
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

    def update_tools(self, new_tools: List[Tool]):
        """Update the active tools list and reinitialize the agent."""
        # Store new tools in generated_tools dictionary
        for tool in new_tools:
            self.generated_tools[tool.name] = tool
        
        # Recreate active_tools list with base tools and all generated tools
        self.active_tools = self.base_tools.copy()
        self.active_tools.extend(self.generated_tools.values())
        
        # Reinitialize the agent with updated tools
        self.agent = self._create_agent()
        return True     
    def process_input(self, user_input: str):
        """Process user input and handle dynamic tool updates."""
        # Get initial response
        agent_response = self.agent(user_input)
        
        # Check if the response contains new tools from ToolGen
        if isinstance(agent_response, dict) and 'tools' in agent_response:
            new_tools = agent_response['tools']
            if new_tools:
                # Update tools and reinitialize agent
                self.update_tools(new_tools)
                # Re-run the query with updated tools
                agent_response = self.agent(user_input)
        
        # Extract details for chat history
        thought = agent_response.get("thought", "No thought recorded")
        action = agent_response.get("action", "No action recorded")
        observation = agent_response.get("observation", "No observation recorded")
        final_answer = agent_response.get("output", "No final answer")
        
        # Save chat history
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