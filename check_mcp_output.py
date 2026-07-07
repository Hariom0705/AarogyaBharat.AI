import subprocess
import sys
import os

mcp_server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "mcp_server.py")
print("mcp_server_path:", mcp_server_path)

proc = subprocess.Popen(
    [sys.executable, "-u", mcp_server_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send initialize request
req = '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}\n'
proc.stdin.write(req)
proc.stdin.flush()

# Wait a second and read stderr
import time
time.sleep(2)
if proc.poll() is None:
    print("Process is still running!")
    proc.terminate()
else:
    print("Process exited!")
print("Exit code:", proc.returncode)
print("STDERR:")
print(proc.stderr.read() if proc.stderr else "No stderr")
print("STDOUT:")
print(proc.stdout.read() if proc.stdout else "No stdout")
