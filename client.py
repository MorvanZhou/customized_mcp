import json
import subprocess
import select
from typing import List
import os


class McpClient:
    def __init__(self, command: str, args: List[str] = None):
        """初始化 MCP 客户端并启动服务器进程"""
        self._msg_id = 0
        if args is None:
            args = []
        
        self.proc = subprocess.Popen(
            args=[command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        self.initialize_server()

    def initialize_server(self):
        """初始化服务器"""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "sampling": {},
                "roots": {"listChanged": True}
            },
            "clientInfo": {
                "name": "mcp-inspector",
                "version": "0.8.1"
            }
        }
        self.send_request(method="initialize", params=params)
        self.send_request(method="notifications/initialized")

    def send_request(self, method: str, params: dict = None):
        data = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if method == "initialize":
            data["id"] = 0
            data["params"] = params
        elif method == "notifications/initialized":
            pass
        else:
            data["id"] = self._msg_id + 1
            data["params"] = params if params else {}
            self._msg_id += 1
            
        request = json.dumps(data) + "\n"
        self.proc.stdin.write(request.encode())
        self.proc.stdin.flush()
        
        ready = select.select([self.proc.stdout], [], [], 1)
        if ready[0]:
            response = self.proc.stdout.readline().decode()
            try:
                parsed_response = json.loads(response)
                return json.dumps(parsed_response, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                return f"Failed to parse initialization response: {response}"
        else:
            return "No response received from server"
            
    def call_tool(self, name: str, args: dict = None):
        _p = {
            "arguments": args if args else {},
            "name": name,
        }
        return self.send_request(method="tools/call", params=_p)
    
    def list_tools(self):
        """获取工具列表"""
        response = self.send_request(method="tools/list", params={})
        parsed_response = json.loads(response)
        return json.dumps(parsed_response, indent=2, ensure_ascii=False)
    
    def terminate(self):
        """终止服务器进程"""
        self.proc.terminate()

# 示例用法
if __name__ == "__main__":
    client = McpClient(
        command=os.path.join(os.path.abspath(os.path.curdir), ".venv", "bin", "python"),
        args=["server.py"]
    )
    try:
        # 发送工具列表请求
        response = client.list_tools()
        print(response)

        # 示例：发送天气请求
        response = client.call_tool(name="get_weather", args={"city": "北京"})
        print(response)

    finally:
        client.terminate()