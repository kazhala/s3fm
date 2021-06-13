"""Module contains all searching related helper functions."""
from typing import Dict, List, Optional

from Levenshtein import *  # type: ignore

from s3fm.api.fs import File


async def match_exact(files: List[File], text: str) -> Optional[Dict[int, List[int]]]:
    """Leverage levenshtein distance to find partial exact matches.

    TODO: CASE in-sensitive search

    Args:
        files: List of files to search.
        text: Search text.

    Returns:
        Optional dictionary of sets of matched index and matching indicies.
    """
    result = None
    for i in range(len(files)):
        file = files[i]
        if len(text) > len(file.name):
            continue

        blocks = matching_blocks(editops(text, file.name), text, file.name)  # type: ignore
        if len(blocks) != 2:
            continue
        match = blocks[0]
        if match[2] == len(text):
            if result is None:
                result = {}
            result[i] = {j for j in range(match[1], match[1] + match[2])}
    return result
