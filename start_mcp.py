#!/usr/bin/env python3
"""
Start MCP Server with Complete Warning Suppression
"""

# Step 1: Completely silence warnings before ANY imports
import sys
import os
import warnings

# Set environment variables
os.environ['PAPERSCRAPER_MCP_MODE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'

# Override warning system completely
def warn(*args, **kwargs):
    pass

warnings.warn = warn
warnings.warn_explicit = warn
warnings.filterwarnings('ignore')

# Step 2: Redirect stderr temporarily during imports
import io
_real_stderr = sys.stderr
sys.stderr = io.StringIO()

try:
    # Step 3: Now import with stderr captured
    import asyncio
    from paperscraper.mcp_server import main
finally:
    # Step 4: Restore stderr for debugging
    sys.stderr = _real_stderr

# Step 5: Run the server
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)