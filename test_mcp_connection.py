#!/usr/bin/env python3
"""Test MCP connection by sending initialize request."""

import subprocess
import json
import sys

# Send initialize request
initialize_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

# Start the MCP server
proc = subprocess.Popen(
    ["/Users/matthiasflo/opt/miniconda3/envs/geo-mcp-server/bin/paperscraper-mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send request
request_str = json.dumps(initialize_request)
print(f"Sending: {request_str}")
proc.stdin.write(request_str + "\n")
proc.stdin.flush()

# Read response
try:
    response = proc.stdout.readline()
    print(f"Response: {response}")
    
    # Try to parse as JSON
    if response:
        response_data = json.loads(response)
        print(f"Parsed response: {json.dumps(response_data, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    stderr = proc.stderr.read()
    if stderr:
        print(f"Stderr: {stderr}")

# Clean up
proc.terminate()