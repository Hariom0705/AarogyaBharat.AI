import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.agent import app
from google.adk.runners import run_async

async def main():
    print("Testing locally...")
    query = "I have a severe headache and blurry vision since morning."
    
    try:
        async for event in run_async(app.root_agent, input=query):
            if hasattr(event, "output") and event.output:
                print(repr(event.output))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
