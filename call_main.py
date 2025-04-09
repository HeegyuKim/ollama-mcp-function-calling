from pprint import pprint
import asyncio
import sys
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Tuple

import ollama
import requests
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

def print_items(name: str, result: Any) -> None:
    """Print items with formatting.

    Args:
        name: Category name (tools/resources/prompts)
        result: Result object containing items list
    """
    print("", f"Available {name}:", sep="\n")
    items = getattr(result, name)
    if items:
        for item in items:
            print(" *", item)
    else:
        print("No items available")

def mcp_tool_to_dict(tool):
    prop = {}
    for k, v in tool.inputSchema["properties"].items():
        prop[k] = {
            "type": v["type"],
            "description": v["title"]
        }

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "required": tool.inputSchema["required"],
                "properties": prop
            }
        }
    }

async def main(server_url: str = "http://localhost:8000/sse"):
    async with sse_client(server_url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            print("Connected to MCP server at", server_url)
            tools = await session.list_tools()
            tools = [mcp_tool_to_dict(tool) for tool in tools.tools]
            
            for tool in tools:
                pprint(tool)

            messages=[{
                'role': 'user',
                'content': 'How is the weather in LA, California?'
            }]

            response = ollama.chat(
                'qwen2.5',
                messages=messages,    
                tools=tools
            )

            if response.message.content:
                print("Response:", response.message.content)

            if response.message.tool_calls:
                print("Tool calls:")
                for call in response.message.tool_calls:
                    print("Tool name:", call.function.name)
                    print("Arguments:", call.function.arguments)

                    output = await session.call_tool(
                        call.function.name,
                        arguments=call.function.arguments
                    )
                    output = output.content[0].text
                    print("Tool output:", output)

                    messages.append({
                        'role': 'tool',
                        'content': output
                    })

                    response = ollama.chat(
                        'qwen2.5',
                        messages=messages,
                        tools=tools
                    )
                    print("Response:", response.message.content)


    # result = await session.call_tool("tool-name", arguments={"arg1": "value"})




if __name__ == "__main__":
    asyncio.run(main())
