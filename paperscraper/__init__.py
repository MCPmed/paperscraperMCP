"""Initialize the module."""

__name__ = "paperscraper"
__version__ = "0.3.2"

import logging
import os
import sys
from typing import List, Union

# Check if we're in MCP mode before importing load_dumps
# In MCP mode, delay load_dumps import to avoid stdout warnings
# import sys
# print(f"DEBUG __init__.py: MCP mode = {os.environ.get('PAPERSCRAPER_MCP_MODE')}", file=sys.stderr)

if not os.environ.get('PAPERSCRAPER_MCP_MODE'):
    from .load_dumps import QUERY_FN_DICT
else:
    # In MCP mode, defer the import and create a lazy loader
    QUERY_FN_DICT = None
from .utils import get_filename_from_query

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger(__name__)

# Set urllib logging depth
url_logger = logging.getLogger("urllib3")
url_logger.setLevel(logging.WARNING)
# Set arxiv logging depth
arxiv_logger = logging.getLogger("arxiv")
arxiv_logger.setLevel(logging.WARNING)


def dump_queries(keywords: List[List[Union[str, List[str]]]], dump_root: str) -> None:
    """Performs keyword search on all available servers and dump the results.

    Args:
        keywords (List[List[Union[str, List[str]]]]): List of lists of keywords
            Each second-level list is considered a separate query. Within each
            query, each item (whether str or List[str]) are considered AND
            separated. If an item is again a list, strs are considered synonyms
            (OR separated).
        dump_root (str): Path to root for dumping.
    """
    global QUERY_FN_DICT
    
    # Import QUERY_FN_DICT if not already available (MCP mode)
    if QUERY_FN_DICT is None:
        from .load_dumps import QUERY_FN_DICT

    for idx, keyword in enumerate(keywords):
        for db, f in QUERY_FN_DICT.items():
            logger.info(f" Keyword {idx + 1}/{len(keywords)}, DB: {db}")
            filename = get_filename_from_query(keyword)
            os.makedirs(os.path.join(dump_root, db), exist_ok=True)
            f(keyword, output_filepath=os.path.join(dump_root, db, filename))
