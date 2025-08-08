# paperscraper MCP Server

An MCP (Model Context Protocol) server that enables Large Language Models to search and retrieve academic papers from PubMed, arXiv, bioRxiv, medRxiv, chemRxiv, and Google Scholar.

## Acknowledgments

This MCP server is built on top of the excellent [paperscraper](https://github.com/jannisborn/paperscraper) library by [@jannisborn](https://github.com/jannisborn) and contributors. The core paper scraping functionality comes from that implementation. 

**Note:** This is an early version of the MCP integration and the code is currently quite messy. A cleaner implementation is coming soon!

## Table of Contents

1. [Installation](#installation)
2. [MCP Server Setup](#mcp-server-setup)
3. [Available Functions](#available-functions)
4. [Usage Examples](#usage-examples)
5. [Database Setup](#database-setup)
   - [Download Preprint Server Dumps](#download-preprint-server-dumps)
   - [Local arXiv Dump](#local-arxiv-dump)
6. [Original paperscraper Features](#original-paperscraper-features)

## Installation

```bash
pip install paperscraper mcp
```

## MCP Server Setup

To use paperscraper with an LLM client that supports MCP (such as Claude Desktop), add the following to your MCP configuration:

```json
{
  "mcpServers": {
    "paperscraper-server": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "paperscraper.mcp_server"],
      "env": {}
    }
  }
}
```

## Available Functions

The MCP server provides the following functions for paper searching and retrieval:

- **search_pubmed**: Search PubMed database using keyword queries with AND/OR logic
- **search_arxiv**: Search arXiv database using keyword queries with AND/OR logic
- **search_scholar**: Search Google Scholar using topic-based queries
- **search_preprint_servers**: Search bioRxiv, medRxiv, and chemRxiv preprint servers
- **get_citations**: Get citation count for a paper by title or DOI
- **search_journal_impact**: Search for journal impact factors
- **download_paper_pdf**: Download PDF of a paper using its DOI
- **update_preprint_dumps**: Update local dumps of preprint servers

## Usage Examples

Once configured, you can ask your LLM to:

- "Search PubMed for papers on COVID-19 and artificial intelligence"
- "Find recent arXiv papers on transformer models in computer vision"
- "Get the citation count for 'Attention is All You Need'"
- "Download the PDF for DOI 10.1234/example"
- "Search bioRxiv for papers on CRISPR from 2023"

## Database Setup

### Download Preprint Server Dumps

To search preprint servers (bioRxiv, medRxiv, chemRxiv), you need to download their dumps first. These are stored locally in `.jsonl` format:

```py
from paperscraper.get_dumps import biorxiv, medrxiv, chemrxiv
medrxiv()  #  Takes ~30min and should result in ~35 MB file
biorxiv()  # Takes ~1h and should result in ~350 MB file
chemrxiv()  #  Takes ~45min and should result in ~20 MB file
```

You can also update dumps for specific date ranges:
```py
medrxiv(start_date="2023-04-01", end_date="2023-04-08")
```

### Local arXiv Dump

For faster arXiv searches, you can create a local dump instead of using the API:

```py
from paperscraper.get_dumps import arxiv
arxiv(start_date='2024-01-01', end_date=None) # scrapes all metadata from 2024 until today.
```

## Original paperscraper Features

For detailed documentation on the underlying paperscraper functionality, including:
- Direct Python API usage
- Advanced search queries with Boolean logic
- Full-text PDF/XML retrieval
- Citation counting
- Journal impact factor lookup
- Data visualization (bar plots, Venn diagrams)
- Publisher API integration (Wiley, Elsevier)

Please visit the original [paperscraper repository](https://github.com/jannisborn/paperscraper).

## License and Citation

This project uses the paperscraper library. If you use this MCP server in your research, please cite:

```bib
@article{born2021trends,
  title={Trends in Deep Learning for Property-driven Drug Design},
  author={Born, Jannis and Manica, Matteo},
  journal={Current Medicinal Chemistry},
  volume={28},
  number={38},
  pages={7862--7886},
  year={2021},
  publisher={Bentham Science Publishers}
}
```
