import asyncio
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Ensure we are running from correct dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))
mcp_server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "mcp_server.py")

async def main():
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[mcp_server_path]
    )
    print("Attempting to connect to MCP server...")
    print(f"Using python: {sys.executable}")
    try:
        async with stdio_client(server_parameters) as (read, write):
            async with ClientSession(read, write) as session:
                print("Initializing session...")
                await session.initialize()
                print("Session initialized successfully!")
                tools = await session.list_tools()
                print("Tools found:", tools)
    except Exception as e:
        print("Error encountered:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
