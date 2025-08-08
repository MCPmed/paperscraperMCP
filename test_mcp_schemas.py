#!/usr/bin/env python3
"""Test MCP server schemas for complex types that Claude doesn't support."""

import os
import sys
import json

# Set environment before imports
os.environ['PAPERSCRAPER_MCP_MODE'] = '1'

# Add paperscraper to path
sys.path.insert(0, '/Users/matthiasflo/Documents/paperscraper')

# Import after setting environment
from paperscraper.mcp_server import handle_list_tools as mcp_list_tools
from mcp_server_standalone import handle_list_tools as standalone_list_tools
import asyncio

async def check_schemas():
    """Check both MCP servers for problematic schemas."""
    
    print("Testing paperscraper/mcp_server.py:")
    print("-" * 40)
    
    try:
        tools = await mcp_list_tools()
        for tool in tools:
            schema_str = json.dumps(tool.inputSchema)
            if 'anyOf' in schema_str or 'oneOf' in schema_str:
                print(f"❌ {tool.name}: Has anyOf/oneOf in schema")
                print(f"   Schema: {json.dumps(tool.inputSchema, indent=2)}")
            else:
                print(f"✅ {tool.name}: Schema is simple")
    except Exception as e:
        print(f"Error testing mcp_server.py: {e}")
    
    print("\nTesting mcp_server_standalone.py:")
    print("-" * 40)
    
    try:
        tools = await standalone_list_tools()
        for tool in tools:
            schema_str = json.dumps(tool.inputSchema)
            if 'anyOf' in schema_str or 'oneOf' in schema_str:
                print(f"❌ {tool.name}: Has anyOf/oneOf in schema")
                print(f"   Schema: {json.dumps(tool.inputSchema, indent=2)}")
            else:
                print(f"✅ {tool.name}: Schema is simple")
    except Exception as e:
        print(f"Error testing mcp_server_standalone.py: {e}")

if __name__ == "__main__":
    asyncio.run(check_schemas())