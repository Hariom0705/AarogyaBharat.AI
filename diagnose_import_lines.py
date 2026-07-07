import sys
import time
import os

# Ensure unbuffered print
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, "reconfigure") else None

def trace_lines(frame, event, arg):
    if event == 'line':
        code = frame.f_code
        filename = code.co_filename
        if "fast_api_app.py" in filename:
            line_no = frame.f_lineno
            print(f"Line {line_no} starting...")
            sys.stdout.flush()
    return trace_lines

sys.settrace(trace_lines)

print("Starting import trace...")
import app.fast_api_app
print("Import complete!")
