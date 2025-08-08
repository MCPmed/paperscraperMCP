#!/usr/bin/env python3
"""
MCP Server Wrapper for Paperscraper
This wrapper ensures complete isolation of stdout for JSON-RPC communication.
"""

import os
import sys

# Create a null output class
class NullWriter:
    def write(self, msg):
        pass
    def flush(self):
        pass
    def fileno(self):
        return -1
    @property
    def buffer(self):
        return self

_original_stderr = sys.stderr
_original_stdout = sys.stdout

# Redirect ALL output to null temporarily
sys.stdout = NullWriter()
sys.stderr = sys.stderr  # Keep stderr for debugging

# Set environment variables before ANY imports
os.environ['PAPERSCRAPER_MCP_MODE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress all warnings at the earliest point
import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')

# Now import the MCP server module
try:
    # Import and run the main function
    from paperscraper.mcp_server import main
    import asyncio
    
    # Restore stderr for error messages
    sys.stderr = _original_stderr
    
    # Restore stdout for JSON-RPC
    sys.stdout = _original_stdout
    
    # Run the server
    asyncio.run(main())
    
except KeyboardInterrupt:
    pass
except Exception as e:
    # Restore stderr to report errors
    sys.stderr = _original_stderr
    print(f"Fatal error: {e}", file=sys.stderr)
    sys.exit(1)