import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="my mcp",
    log_level="ERROR",
)

project_dir = os.path.abspath(os.path.curdir)

@mcp.tool()
def get_project_files():
    """get project files"""
    return os.listdir(os.path.expanduser(project_dir))

@mcp.tool()
def read_file(file: str):
    """读取项目文件内容"""
    with open(os.path.join(project_dir, file), 'r') as f:
        return f.read()
    
@mcp.tool()
def get_weather(city: str):
    """get weather for city"""
    import random
    return f"{city}的天气是{random.choice(['晴天', '阴天', '雨天'])}"

    
if __name__ == "__main__":
    mcp.run(transport="stdio")
    
    

