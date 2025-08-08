#!/usr/bin/env python3
"""
Clean MCP Server for Paperscraper
"""

import os
import sys

# Critical: Set environment before ANY imports
os.environ['PAPERSCRAPER_MCP_MODE'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')
# Specifically ignore pkg_resources deprecation warning
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='pkg_resources is deprecated')

# Configure logging before imports
import logging
logging.basicConfig(level=logging.CRITICAL)
logging.disable(logging.CRITICAL)

# Monkey-patch print to prevent any output to stdout
_original_print = print
def _silent_print(*args, **kwargs):
    if kwargs.get('file') == sys.stdout:
        kwargs['file'] = sys.stderr
    _original_print(*args, **kwargs)
print = _silent_print

# Now run the actual server
if __name__ == "__main__":
    from paperscraper.mcp_server import main
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import sys
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)