# Paperscraper MCP Integration

This document describes how to use paperscraper as a Model Context Protocol (MCP) server, enabling seamless integration with Claude and other LLMs.

## Overview

The paperscraper MCP server provides access to academic paper search functionality through a standardized interface. This allows LLMs to:

- Search papers across multiple databases (PubMed, arXiv, Google Scholar, preprint servers)
- Retrieve citation counts
- Look up journal impact factors  
- Download paper PDFs
- Update preprint server databases

## Installation

### Prerequisites

- Python 3.8 or higher
- MCP Python SDK

### Install paperscraper with MCP support

```bash
pip install paperscraper[mcp]
```

Or install the MCP dependencies separately:

```bash
pip install paperscraper mcp fastmcp
```

## Configuration

### For Claude Desktop

Add the following to your Claude Desktop MCP configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "paperscraper": {
      "command": "python",
      "args": ["-m", "paperscraper.mcp_server"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### For other MCP clients

Use the provided `mcp_config.json` file or create your own configuration.

## Running the Server

### Standalone mode
```bash
python -m paperscraper.mcp_server
```

### As part of Claude Desktop
The server will start automatically when Claude Desktop launches with the proper configuration.

## Available Tools

### 1. search_pubmed
Search for papers in the PubMed database.

**Parameters:**
- `query`: List of keyword groups (AND/OR logic)
- `max_results`: Maximum number of results (default: 100)

**Example:**
```python
query = [["COVID-19", "SARS-CoV-2"], ["machine learning", "AI"]]
```

### 2. search_arxiv  
Search for papers in the arXiv database.

**Parameters:**
- `query`: List of keyword groups
- `max_results`: Maximum number of results (default: 100)

### 3. search_scholar
Search Google Scholar for papers.

**Parameters:**
- `topic`: Search topic (string)
- `max_results`: Maximum number of results (default: 50)

### 4. search_preprint_servers
Search bioRxiv, medRxiv, and chemRxiv preprint servers.

**Parameters:**
- `query`: List of keyword groups
- `servers`: Which servers to search (default: all)

### 5. get_citations
Get citation count for a paper.

**Parameters:**
- `title`: Paper title (optional)
- `doi`: Paper DOI (optional)

### 6. search_journal_impact
Search for journal impact factors.

**Parameters:**
- `journal_name`: Journal name to search
- `threshold`: Fuzzy search threshold (default: 85)
- `min_impact`: Minimum impact factor (default: 0)
- `max_impact`: Maximum impact factor (optional)

### 7. download_paper_pdf
Download PDF of a paper using its DOI.

**Parameters:**
- `doi`: DOI of the paper
- `filename`: Optional filename for the PDF

### 8. update_preprint_dumps
Update local dumps of preprint servers.

**Parameters:**
- `servers`: Which servers to update (default: all)
- `start_date`: Start date for selective update (YYYY-MM-DD)
- `end_date`: End date for selective update (YYYY-MM-DD)

## Usage Examples

Once configured, you can use natural language with Claude to interact with paperscraper:

> "Search for recent papers about machine learning in drug discovery on PubMed"

> "Find papers about quantum computing on arXiv from the last year"

> "What's the impact factor of Nature Communications?"

> "Get citation count for the paper titled 'Attention Is All You Need'"

> "Download the PDF for DOI 10.48550/arXiv.2207.03928"

## Setup for Preprint Servers

Before searching preprint servers, you need to download their databases:

```python
from paperscraper.get_dumps import biorxiv, medrxiv, chemrxiv

# Download full databases (first time setup)
medrxiv()   # ~30min, ~35 MB
biorxiv()   # ~1h, ~350 MB  
chemrxiv()  # ~45min, ~20 MB
```

Or use the MCP tool:
> "Update the preprint dumps for all servers"

## Troubleshooting

### Common Issues

1. **ImportError**: Make sure all dependencies are installed
   ```bash
   pip install mcp fastmcp
   ```

2. **Server not found**: Check that the path in your MCP configuration is correct

3. **No results from preprint servers**: Make sure dumps are downloaded first

4. **Google Scholar rate limiting**: Scholar searches may be limited due to rate limiting/captchas

### Logging

The server logs to stdout by default. Set logging level:

```python
import logging
logging.getLogger("paperscraper-mcp").setLevel(logging.DEBUG)
```

## Advanced Configuration

### Custom API Keys

For enhanced PDF downloading with publisher APIs, create a `.env` file:

```
WILEY_TDM_API_TOKEN=your_wiley_token
ELSEVIER_TDM_API_KEY=your_elsevier_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

### Custom Preprint Dump Location

Set the `PAPERSCRAPER_DUMP_DIR` environment variable to customize where preprint dumps are stored.

## Contributing

Contributions to improve the MCP integration are welcome! Please see the main repository for contribution guidelines.

## License

MIT License - see LICENSE file for details.