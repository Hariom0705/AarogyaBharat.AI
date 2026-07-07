import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Setting event loop policy...")
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

print("Importing app...")
from app.fast_api_app import app

print("Running uvicorn...")
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=18081)
