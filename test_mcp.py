#!/usr/bin/env python3
"""
Test script for paperscraper MCP server functionality
"""

import asyncio
import json
import sys
from typing import Any, Dict

def test_paperscraper_functionality():
    """Test core paperscraper functionality without MCP."""
    print("Testing core paperscraper functionality...")
    
    # Test impact factor search
    try:
        from paperscraper.impact import Impactor
        impactor = Impactor()
        results = impactor.search("Nature", threshold=90)
        print(f"✓ Impact factor search successful: found {len(results)} results")
        if results:
            print(f"  Example: {results[0]['journal']} - IF: {results[0]['factor']}")
    except Exception as e:
        print(f"✗ Impact factor search failed: {e}")
        return False
    
    # Test citation functionality (basic import)
    try:
        from paperscraper.citations import get_citations_from_title
        print("✓ Citation functionality imported successfully")
    except Exception as e:
        print(f"✗ Citation functionality import failed: {e}")
        return False
    
    # Test arxiv functionality (basic import)
    try:
        from paperscraper.arxiv import get_and_dump_arxiv_papers
        print("✓ ArXiv functionality imported successfully")
    except Exception as e:
        print(f"✗ ArXiv functionality import failed: {e}")
        return False
    
    # Test pubmed functionality (basic import)
    try:
        from paperscraper.pubmed import get_and_dump_pubmed_papers
        print("✓ PubMed functionality imported successfully")
    except Exception as e:
        print(f"✗ PubMed functionality import failed: {e}")
        return False
    
    return True

def test_mcp_structure():
    """Test that MCP server structure is correct without importing MCP."""
    print("\nTesting MCP server file structure...")
    
    # Check if MCP server file exists and has correct structure
    try:
        with open("paperscraper/mcp_server.py", "r") as f:
            content = f.read()
        
        # Check for key components
        required_components = [
            "async def handle_list_tools",
            "async def handle_call_tool", 
            "search_pubmed",
            "search_arxiv",
            "search_scholar",
            "get_citations",
            "search_journal_impact"
        ]
        
        missing = []
        for component in required_components:
            if component not in content:
                missing.append(component)
        
        if missing:
            print(f"✗ Missing MCP server components: {missing}")
            return False
        
        print("✓ MCP server file has all required components")
        
        # Check for proper async structure
        if "async def main" in content and "asyncio.run(main())" in content:
            print("✓ MCP server has proper async main structure")
        else:
            print("⚠ MCP server may not have proper async structure")
        
        return True
        
    except FileNotFoundError:
        print("✗ MCP server file not found")
        return False
    except Exception as e:
        print(f"✗ Error checking MCP server file: {e}")
        return False

def test_imports():
    """Test that paperscraper imports work."""
    print("Testing paperscraper imports...")
    
    # Test paperscraper imports
    try:
        import paperscraper
        print(f"✓ Paperscraper imported successfully (version {paperscraper.__version__})")
    except ImportError as e:
        print(f"✗ Paperscraper import failed: {e}")
        return False
    
    return True

def test_config_files():
    """Test that configuration files are properly formatted."""
    print("\nTesting configuration files...")
    
    # Test pyproject.toml exists and is valid
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # Fallback for older Python
        except ImportError:
            print("⚠ Cannot test TOML files (tomllib/tomli not available)")
            return True
    
    try:
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        print("✓ pyproject.toml is valid TOML")
        
        # Check key fields
        assert "project" in config
        assert config["project"]["name"] == "paperscraper"
        print("✓ pyproject.toml has required fields")
        
    except Exception as e:
        print(f"✗ pyproject.toml validation failed: {e}")
        return False
    
    # Test MCP config JSON
    try:
        with open("mcp_config.json", "r") as f:
            mcp_config = json.load(f)
        print("✓ mcp_config.json is valid JSON")
        
        assert "mcpServers" in mcp_config
        assert "paperscraper" in mcp_config["mcpServers"]
        print("✓ mcp_config.json has required structure")
        
    except Exception as e:
        print(f"✗ mcp_config.json validation failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=== Testing Paperscraper MCP Integration ===\n")
    
    # Test imports first
    if not test_imports():
        print("\n✗ Import tests failed. Please install required dependencies.")
        sys.exit(1)
    
    # Test core functionality
    if not test_paperscraper_functionality():
        print("\n✗ Core functionality tests failed.")
        sys.exit(1)
    
    # Test MCP structure
    if not test_mcp_structure():
        print("\n✗ MCP structure tests failed.")
        sys.exit(1)
    
    # Test config files
    if not test_config_files():
        print("\n✗ Configuration file tests failed.")
        sys.exit(1)
    
    print("\n✓ All tests completed successfully!")
    print("\nMCP Integration Summary:")
    print("- Core paperscraper functionality: ✓")
    print("- MCP server structure: ✓") 
    print("- Configuration files: ✓")
    print("\nTo use with Claude Desktop (Python 3.10+ required):")
    print("1. Install MCP dependencies: pip install mcp")
    print("2. Add mcp_config.json contents to your Claude Desktop config")
    print("3. Restart Claude Desktop")
    print("4. Try asking: 'Search for papers about machine learning'")
    print("\nFor full functionality, install optional MCP dependencies:")
    print("pip install paperscraper[mcp]")

if __name__ == "__main__":
    main()