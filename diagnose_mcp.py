import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
mcp_server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "mcp_server.py")
print("mcp_server_path:", mcp_server_path)

proc = subprocess.Popen(
    [sys.executable, "-u", mcp_server_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

print("Started process...")
try:
    req = '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}\n'
    stdout, stderr = proc.communicate(input=req, timeout=5)
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
except subprocess.TimeoutExpired as e:
    proc.kill()
    stdout, stderr = proc.communicate()
    print("TIMEOUT!")
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
