# Customized MCP Project

This project leverages the `mcp` library with CLI support and integrates with OpenAI's API.

## Requirements

Make sure to install the required dependencies before running the project:

```bash
pip install -r requirements.txt
```

## Usage

1. Configure your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. Start the MCP server:
   ```bash
   python server.py
   ```

3. Use the client to interact with the server:
   ```bash
   python client.py
   ```

4. Alternatively, use the orchestrator to query the LLM and tools:
   ```bash
   python main.py
   ```

## Example

### Querying the Weather Tool
Run the client and call the `get_weather` tool:
```bash
python client.py
```

Example interaction:
```
You: List tools
Assistant: {
  "tools": [
    {
      "name": "get_weather",
      "description": "Get weather for a city",
      "parameters": {
        "city": {
          "type": "string",
          "description": "Name of the city"
        }
      }
    }
  ]
}

You: Call get_weather with {"city": "Beijing"}
Assistant: 北京的天气是晴天
```

## Dependencies

- `openai==1.70.0`
- `mcp[cli]==1.6.0`

## License

This project is licensed under the MIT License.