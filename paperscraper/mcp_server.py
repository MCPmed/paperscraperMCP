#!/usr/bin/env python3
"""
MCP Server for Paperscraper

This server provides access to paperscraper functionality through the Model Context Protocol,
enabling LLMs to search for academic papers across multiple databases.
"""

# CRITICAL: Set MCP mode environment variable BEFORE any imports
# This must be the very first thing that happens
import os
os.environ['PAPERSCRAPER_MCP_MODE'] = '1'

# Configure logging and warnings FIRST before any other imports
import sys
import warnings
import logging

# Suppress ALL warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Completely suppress warnings by overriding the warnings module
def _ignore_warnings(*args, **kwargs):
    pass
warnings.warn = _ignore_warnings
warnings.warn_explicit = _ignore_warnings

# Redirect stdout to stderr to prevent any print statements from breaking JSON-RPC
original_stdout = sys.stdout
sys.stdout = sys.stderr

# Set up minimal logging
logging.basicConfig(
    level=logging.CRITICAL,  # Only show critical errors
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Override the logging module's basicConfig to prevent modules from changing it
original_basicConfig = logging.basicConfig
def dummy_basicConfig(*args, **kwargs):
    pass
logging.basicConfig = dummy_basicConfig

# Suppress ALL logging from paperscraper and related libraries
logging.getLogger().setLevel(logging.CRITICAL)
for logger_name in ["scholarly", "paperscraper", "mcp", "urllib3", "requests", "paperscraper.load_dumps"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.disabled = True

# Now import everything else
import asyncio
import json
import tempfile
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Import individual modules directly without triggering package __init__.py
import sys
import importlib.util

# Import paperscraper modules
from paperscraper.pubmed import get_and_dump_pubmed_papers
from paperscraper.arxiv import get_and_dump_arxiv_papers
from paperscraper.scholar import get_and_dump_scholar_papers
from paperscraper.xrxiv.xrxiv_query import XRXivQuery
from paperscraper.citations import get_citations_from_title, get_citations_by_doi
from paperscraper.impact import Impactor
from paperscraper.pdf import save_pdf, save_pdf_from_dump
from paperscraper.utils import load_jsonl
from paperscraper.get_dumps import biorxiv, medrxiv, chemrxiv
from paperscraper.load_dumps import QUERY_FN_DICT

# load_dumps_module was imported directly with MCP mode, so no logger override needed

logger = logging.getLogger("paperscraper-mcp")

# Initialize the MCP server
server = Server("paperscraper")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available paperscraper tools."""
    return [
        Tool(
            name="search_pubmed",
            description="Search for papers in PubMed database using keyword queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "array",
                        "description": "List of keyword groups for AND/OR search. Each group contains synonyms (OR), groups are combined with AND",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_arxiv",
            description="Search for papers in arXiv database using keyword queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "array",
                        "description": "List of keyword groups for AND/OR search. Each group contains synonyms (OR), groups are combined with AND",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_scholar",
            description="Search for papers in Google Scholar using a topic query",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to search for (like Google Scholar search)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 50
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="search_preprint_servers",
            description="Search bioRxiv, medRxiv, and chemRxiv preprint servers",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "array",
                        "description": "List of keyword groups for AND/OR search",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "servers": {
                        "type": "array",
                        "description": "Which preprint servers to search",
                        "items": {
                            "type": "string",
                            "enum": ["biorxiv", "medrxiv", "chemrxiv"]
                        },
                        "default": ["biorxiv", "medrxiv", "chemrxiv"]
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_citations",
            description="Get citation count for a paper by title or DOI",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Paper title to search for citations"
                    },
                    "doi": {
                        "type": "string",
                        "description": "DOI of the paper"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_journal_impact",
            description="Search for journal impact factors",
            inputSchema={
                "type": "object",
                "properties": {
                    "journal_name": {
                        "type": "string",
                        "description": "Journal name to search for"
                    },
                    "threshold": {
                        "type": "integer",
                        "description": "Fuzzy search threshold (100 = exact match)",
                        "default": 85
                    },
                    "min_impact": {
                        "type": "number",
                        "description": "Minimum impact factor",
                        "default": 0
                    },
                    "max_impact": {
                        "type": "number",
                        "description": "Maximum impact factor"
                    }
                },
                "required": ["journal_name"]
            }
        ),
        Tool(
            name="download_paper_pdf",
            description="Download PDF of a paper using its DOI",
            inputSchema={
                "type": "object",
                "properties": {
                    "doi": {
                        "type": "string",
                        "description": "DOI of the paper to download"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the PDF"
                    }
                },
                "required": ["doi"]
            }
        ),
        Tool(
            name="update_preprint_dumps",
            description="Update local dumps of preprint servers (biorxiv, medrxiv, chemrxiv)",
            inputSchema={
                "type": "object",
                "properties": {
                    "servers": {
                        "type": "array",
                        "description": "Which servers to update",
                        "items": {
                            "type": "string",
                            "enum": ["biorxiv", "medrxiv", "chemrxiv"]
                        },
                        "default": ["biorxiv", "medrxiv", "chemrxiv"]
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for selective update (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for selective update (YYYY-MM-DD)"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    try:
        if name == "search_pubmed":
            return await search_pubmed(arguments)
        elif name == "search_arxiv":
            return await search_arxiv(arguments)
        elif name == "search_scholar":
            return await search_scholar(arguments)
        elif name == "search_preprint_servers":
            return await search_preprint_servers(arguments)
        elif name == "get_citations":
            return await get_citations(arguments)
        elif name == "search_journal_impact":
            return await search_journal_impact(arguments)
        elif name == "download_paper_pdf":
            return await download_paper_pdf(arguments)
        elif name == "update_preprint_dumps":
            return await update_preprint_dumps(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error in {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def search_pubmed(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search PubMed for papers."""
    query = arguments["query"]
    max_results = arguments.get("max_results", 100)
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
        temp_file = f.name
    
    try:
        get_and_dump_pubmed_papers(
            query, 
            output_filepath=temp_file,
            max_results=max_results
        )
        
        results = load_jsonl(temp_file)
        
        response = f"Found {len(results)} papers in PubMed\n\n"
        for i, paper in enumerate(results[:10]):  # Show first 10
            response += f"{i+1}. {paper.get('title', 'No title')}\n"
            response += f"   Authors: {paper.get('authors', 'Unknown')}\n"
            response += f"   Journal: {paper.get('journal', 'Unknown')}\n"
            response += f"   Year: {paper.get('date', 'Unknown')}\n"
            if paper.get('doi'):
                response += f"   DOI: {paper['doi']}\n"
            response += "\n"
            
        if len(results) > 10:
            response += f"... and {len(results) - 10} more results\n"
            
        return [TextContent(type="text", text=response)]
        
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

async def search_arxiv(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search arXiv for papers."""
    query = arguments["query"]
    max_results = arguments.get("max_results", 100)
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
        temp_file = f.name
    
    try:
        get_and_dump_arxiv_papers(
            query, 
            output_filepath=temp_file,
            max_results=max_results
        )
        
        results = load_jsonl(temp_file)
        
        response = f"Found {len(results)} papers in arXiv\n\n"
        for i, paper in enumerate(results[:10]):
            response += f"{i+1}. {paper.get('title', 'No title')}\n"
            response += f"   Authors: {paper.get('authors', 'Unknown')}\n"
            response += f"   Published: {paper.get('date', 'Unknown')}\n"
            if paper.get('doi'):
                response += f"   DOI: {paper['doi']}\n"
            if paper.get('url'):
                response += f"   URL: {paper['url']}\n"
            response += "\n"
            
        if len(results) > 10:
            response += f"... and {len(results) - 10} more results\n"
            
        return [TextContent(type="text", text=response)]
        
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

async def search_scholar(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search Google Scholar for papers."""
    topic = arguments["topic"]
    max_results = arguments.get("max_results", 50)
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
        temp_file = f.name
    
    try:
        get_and_dump_scholar_papers(topic, output_filepath=temp_file)
        
        results = load_jsonl(temp_file)
        
        response = f"Found {len(results)} papers in Google Scholar\n\n"
        for i, paper in enumerate(results[:10]):
            response += f"{i+1}. {paper.get('title', 'No title')}\n"
            response += f"   Authors: {paper.get('authors', 'Unknown')}\n"
            response += f"   Year: {paper.get('date', 'Unknown')}\n"
            if paper.get('citations'):
                response += f"   Citations: {paper['citations']}\n"
            response += "\n"
            
        if len(results) > 10:
            response += f"... and {len(results) - 10} more results\n"
            
        return [TextContent(type="text", text=response)]
        
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

async def search_preprint_servers(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search preprint servers."""
    query = arguments["query"]
    servers = arguments.get("servers", ["biorxiv", "medrxiv", "chemrxiv"])
    
    all_results = []
    response = ""
    
    for server in servers:
        if server in QUERY_FN_DICT:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
                temp_file = f.name
            
            try:
                QUERY_FN_DICT[server](query, output_filepath=temp_file)
                results = load_jsonl(temp_file)
                all_results.extend(results)
                
                response += f"\n{server.upper()}: Found {len(results)} papers\n"
                for i, paper in enumerate(results[:5]):  # Show first 5 per server
                    response += f"  {i+1}. {paper.get('title', 'No title')}\n"
                    response += f"     Authors: {paper.get('authors', 'Unknown')}\n"
                    response += f"     Date: {paper.get('date', 'Unknown')}\n"
                    if paper.get('doi'):
                        response += f"     DOI: {paper['doi']}\n"
                    response += "\n"
                    
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    total_response = f"Total papers found across {len(servers)} servers: {len(all_results)}\n" + response
    return [TextContent(type="text", text=total_response)]

async def get_citations(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get citation count for a paper."""
    title = arguments.get("title")
    doi = arguments.get("doi")
    
    try:
        if doi:
            citations = get_citations_by_doi(doi)
            response = f"Citations for DOI {doi}: {citations}"
        elif title:
            citations = get_citations_from_title(title)
            response = f"Citations for '{title}': {citations}"
        else:
            response = "Error: Either title or DOI must be provided"
            
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error retrieving citations: {str(e)}")]

async def search_journal_impact(arguments: Dict[str, Any]) -> List[TextContent]:
    """Search for journal impact factors."""
    journal_name = arguments["journal_name"]
    threshold = arguments.get("threshold", 85)
    min_impact = arguments.get("min_impact", 0)
    max_impact = arguments.get("max_impact")
    
    try:
        impactor = Impactor()
        
        search_args = {
            "threshold": threshold,
            "min_impact": min_impact
        }
        if max_impact:
            search_args["max_impact"] = max_impact
            
        results = impactor.search(journal_name, **search_args)
        
        if not results:
            response = f"No journals found matching '{journal_name}'"
        else:
            response = f"Found {len(results)} journal(s) matching '{journal_name}':\n\n"
            for result in results:
                response += f"• {result['journal']}\n"
                response += f"  Impact Factor: {result['factor']}\n"
                response += f"  Match Score: {result['score']}%\n\n"
                
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error searching journal impact: {str(e)}")]

async def download_paper_pdf(arguments: Dict[str, Any]) -> List[TextContent]:
    """Download PDF of a paper."""
    doi = arguments["doi"]
    filename = arguments.get("filename", f"{doi.replace('/', '_')}.pdf")
    
    try:
        paper_data = {"doi": doi}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, filename)
            success = save_pdf(paper_data, filepath=filepath)
            
            if success and os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                response = f"Successfully downloaded PDF for DOI: {doi}\n"
                response += f"File size: {file_size:,} bytes\n"
                response += f"Saved to temporary location: {filepath}"
            else:
                response = f"Failed to download PDF for DOI: {doi}"
                
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error downloading PDF: {str(e)}")]

async def update_preprint_dumps(arguments: Dict[str, Any]) -> List[TextContent]:
    """Update preprint server dumps."""
    servers = arguments.get("servers", ["biorxiv", "medrxiv", "chemrxiv"])
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    
    response = "Updating preprint server dumps...\n\n"
    
    for server in servers:
        try:
            response += f"Updating {server}... "
            
            if server == "biorxiv":
                if start_date or end_date:
                    biorxiv(start_date=start_date, end_date=end_date)
                else:
                    biorxiv()
            elif server == "medrxiv":
                if start_date or end_date:
                    medrxiv(start_date=start_date, end_date=end_date)
                else:
                    medrxiv()
            elif server == "chemrxiv":
                if start_date or end_date:
                    chemrxiv(start_date=start_date, end_date=end_date)
                else:
                    chemrxiv()
                    
            response += "✓ Complete\n"
            
        except Exception as e:
            response += f"✗ Error: {str(e)}\n"
    
    response += "\nDump update process finished. Please restart to use updated dumps."
    return [TextContent(type="text", text=response)]

async def main():
    """Run the MCP server."""
    # Restore stdout for MCP JSON-RPC communication
    sys.stdout = original_stdout
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="paperscraper",
                server_version="0.3.2",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
                instructions="A server for searching academic papers using paperscraper"
            )
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass