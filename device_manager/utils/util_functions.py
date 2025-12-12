import re
import secrets
import string
from typing import List


def grep(
    text: str,
    pattern: str,
    ignore_case: bool = False,
) -> List[str]:
    """Searches for a pattern in a text and returns the matching lines.

    Args:
        text (str): The text to search.
        pattern (str): The pattern to search for.
        ignore_case (bool, optional): A flag to ignore the case of the pattern.
            Defaults to False.

    Returns:
        List[str]: The lines that match the pattern.
    """
    flags = re.IGNORECASE if ignore_case else 0
    regex = re.compile(pattern, flags)

    matching_lines = [line for line in text.splitlines() if regex.search(line)]
    return matching_lines
