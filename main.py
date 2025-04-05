import json
import os
from typing import List, Dict, Any
from openai import OpenAI

from client import McpClient



class LlmOrchestrator:
    def __init__(
        self,
        llm_api_key: str,
        llm_base_url: str,
        llm_model: str,
        mcp_command: str,
        mcp_args: List[str] = None,
    ):
        """
        Initialize the LLM orchestrator with an LLM API and MCP client.
        
        Args:
            mcp_command: Command to start the MCP server
            mcp_args: Arguments for the MCP server
        """
        self.llm_client = OpenAI(
            api_key=llm_api_key,
            base_url=llm_base_url,
        )
        self.llm_model = llm_model
        self.mcp_client = McpClient(command=mcp_command, args=mcp_args)
        self.available_tools = self._get_available_tools()
        self.conversation_history = []
    
    def _get_available_tools(self) -> Dict[str, Any]:
        """Get and parse the available tools from MCP"""
        tools_response = self.mcp_client.list_tools()
        return json.loads(tools_response)
    
    def _format_tools_for_llm(self) -> str:
        """Format the available tools in a way the LLM can understand"""
        tool_descriptions = []
        
        for tool in self.available_tools.get("result", {}).get("tools", []):
            name = tool.get("name", "")
            description = tool.get("description", "")
            parameters = tool.get("parameters", {})
            
            param_desc = []
            for param_name, param_info in parameters.items():
                param_type = param_info.get("type", "unknown")
                param_desc.append(f"- {param_name} ({param_type}): {param_info.get('description', '')}")
            
            tool_descriptions.append(
                f"Tool: {name}\n"
                f"Description: {description}\n"
                f"Parameters:\n" + "\n".join(param_desc)
            )
        
        return "\n\n".join(tool_descriptions)
    
    def query_llm(self, user_query: str) -> str:
        """
        Send user query to LLM and get response with tool calling decisions
        
        Args:
            user_query: The user's question or request
            
        Returns:
            The LLM's response or tool results
        """
        # Add user query to conversation history
        self.conversation_history.append({"role": "user", "content": user_query})
        
        # Prepare system message with tool information
        system_message = (
            "You are an assistant that helps users by calling appropriate tools. "
            "Here are the tools available to you:\n\n"
            f"{self._format_tools_for_llm()}\n\n"
            "When a user asks a question, determine if you should use a tool. "
            "If yes, respond with JSON in this format:\n"
            "```json\n{\"tool\": \"tool_name\", \"args\": {\"param1\": \"value1\"}}\n```\n"
            "If no tool is needed, respond normally."
        )
        
        # Call LLM API
        completion = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "system", "content": system_message}, *self.conversation_history],
                temperature=0.3,
            )

        llm_response = completion.choices[0].message.content
        
        # Check if LLM wants to call a tool
        try:
            # Try to extract JSON from the response if it contains tool call
            if "```json" in llm_response:
                json_str = llm_response.split("```json")[1].split("```")[0].strip()
                tool_call = json.loads(json_str)
                
                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args", {})
                print(f"Tool: {tool_name} with args {tool_args}")
                
                # Call the tool via MCP
                tool_result = self.mcp_client.call_tool(name=tool_name, args=tool_args)
                
                # Add tool call and result to conversation history
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": f"I'll use the {tool_name} tool to help with this."
                })
                self.conversation_history.append({
                    "role": "system", 
                    "content": f"Tool result: {tool_result}"
                })
                
                # Ask LLM to interpret the tool results
                return self.interpret_tool_result(tool_name, tool_result)
            
            # If no tool call found, just return the LLM response
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            return llm_response
            
        except (json.JSONDecodeError, KeyError) as e:
            # If tool parsing fails, just return the LLM response
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            return llm_response
    
    def interpret_tool_result(self, tool_name: str, tool_result: str) -> str:
        """Ask the LLM to interpret the tool results in a user-friendly way"""
        system_message = (
            "You are an assistant that helps interpret tool results. "
            "Explain the following tool result in a clear, helpful way for the user."
        )
        
        completion = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Tool: {tool_name}\nResult: {tool_result}"}
                    ],
                temperature=0.3,
            )

        interpretation = completion.choices[0].message.content
        
        self.conversation_history.append({"role": "assistant", "content": interpretation})
        return interpretation
    
    def close(self):
        """Clean up resources"""
        self.mcp_client.terminate()
            

if __name__ == "__main__":
    # Initialize the orchestrator
    orchestrator = LlmOrchestrator(
        llm_api_key=os.getenv("OPENAI_API_KEY"),
        llm_base_url="https://api.moonshot.cn/v1",
        llm_model="moonshot-v1-8k",
        mcp_command=os.path.join(os.path.abspath(os.path.curdir), ".venv", "bin", "python"),
        mcp_args=["server.py"],
    )
    
    print("LLM + MCP Assistant initialized. Type 'exit' to quit.")
    
    try:
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                break
                
            response = orchestrator.query_llm(user_input)
            print(f"\nAssistant: {response}")
    
    finally:
        orchestrator.close()