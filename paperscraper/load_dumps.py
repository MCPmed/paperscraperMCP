import glob
import logging
import os
import sys

import pkg_resources

from .arxiv import get_and_dump_arxiv_papers
from .pubmed import get_and_dump_pubmed_papers
from .xrxiv.xrxiv_query import XRXivQuery

# Check for MCP mode and create appropriate logger
mcp_mode = os.environ.get('PAPERSCRAPER_MCP_MODE')

# Create a logger that always checks MCP mode at runtime
class SmartLogger:
    def _should_log(self):
        return not os.environ.get('PAPERSCRAPER_MCP_MODE')
    
    def warning(self, *args, **kwargs):
        if self._should_log():
            logging.getLogger(__name__).warning(*args, **kwargs)
    
    def info(self, *args, **kwargs):
        if self._should_log():
            logging.getLogger(__name__).info(*args, **kwargs)
    
    def error(self, *args, **kwargs):
        if self._should_log():
            logging.getLogger(__name__).error(*args, **kwargs)
    
    def debug(self, *args, **kwargs):
        if self._should_log():
            logging.getLogger(__name__).debug(*args, **kwargs)
    
    def critical(self, *args, **kwargs):
        if self._should_log():
            logging.getLogger(__name__).critical(*args, **kwargs)

# Configure base logging only if not in MCP mode
if not mcp_mode:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Always use SmartLogger
logger = SmartLogger()

# Set up the query dictionary
QUERY_FN_DICT = {
    "arxiv": get_and_dump_arxiv_papers,
    "pubmed": get_and_dump_pubmed_papers,
}
# For biorxiv, chemrxiv and medrxiv search for local dumps
dump_root = pkg_resources.resource_filename("paperscraper", "server_dumps")

# Load dumps - logger will automatically suppress in MCP mode
for db in ["biorxiv", "chemrxiv", "medrxiv"]:
    dump_paths = glob.glob(os.path.join(dump_root, db + "*"))
    if not dump_paths:
        logger.warning(f" No dump found for {db}. Skipping entry.")
        continue
    elif len(dump_paths) > 1:
        logger.info(f" Multiple dumps found for {db}, taking most recent one")
    path = sorted(dump_paths, reverse=True)[0]

    # Handle empty dumped files (e.g. when API is down)
    if os.path.getsize(path) == 0:
        logger.warning(f"Empty dump for {db}. Skipping entry.")
        continue
    querier = XRXivQuery(path)
    if not querier.errored:
        QUERY_FN_DICT.update({db: querier.search_keywords})
        logger.info(f"Loaded {db} dump with {len(querier.df)} entries")

if len(QUERY_FN_DICT) == 2:
    logger.warning(
        " No dumps found for either biorxiv, medrxiv and chemrxiv."
        " Consider using paperscraper.get_dumps.* to fetch the dumps."
    )
