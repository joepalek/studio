"""
unicode_safe.py -- Safe Unicode handling for Windows cp1252 terminals.

Windows terminals default to cp1252 which cannot encode most Unicode chars
(accented letters, em-dashes, combining marks, etc.). Any agent that prints
user-sourced text (book titles, company names, web content) must sanitize
before printing or risk UnicodeEncodeError crashing the process.

Usage:
    from utilities.unicode_safe import safe_print, safe_str, safe_json_load

    safe_print(f'Processing: {title}')           # replaces ? for non-ASCII
    title = safe_str(book.get('title', ''))      # safe to use in f-strings
    data  = safe_json_load('path/to/file.json')  # handles encoding mismatches
"""
import json
import os
import sys
from typing import Any


def safe_str(obj: Any, max_len: int = 0) -> str:
    """
    Convert any object to an ASCII-safe string.

    Non-ASCII characters are replaced with '?'. This is terminal-display only
    — never use this on data you intend to save to JSON (save originals).

    Args:
        obj:     Anything. Lists return first element. None returns ''.
        max_len: If > 0, truncate to this many characters after sanitizing.
    """
    if obj is None:
        return ''
    if isinstance(obj, list):
        obj = obj[0] if obj else ''
    text = str(obj)
    result = text.encode('ascii', errors='replace').decode('ascii')
    if max_len > 0:
        result = result[:max_len]
    return result


def safe_print(*args, sep=' ', end='\n', file=None, **kwargs):
    """
    Drop-in replacement for print() that sanitizes all arguments.

    Converts each argument to ASCII-safe string before printing.
    Use exactly like print():
        safe_print(f'Title: {title}')
        safe_print('Count:', count, 'items')
    """
    safe_args = [safe_str(a) for a in args]
    out = sep.join(safe_args)
    target = file or sys.stdout
    try:
        print(out, end=end, file=target)
    except UnicodeEncodeError:
        # Last resort: encode/decode the whole line
        print(out.encode('ascii', errors='replace').decode('ascii'), end=end, file=target)


def safe_json_load(path: str, encoding: str = 'utf-8') -> Any:
    """
    Load a JSON file with encoding fallbacks.

    Tries utf-8 first, then utf-8-sig (BOM), then latin-1, then
    reads as bytes and replaces bad characters.

    Args:
        path:     Absolute or relative path to the JSON file.
        encoding: Primary encoding to try (default: utf-8).

    Returns:
        Parsed JSON object (dict, list, etc.).

    Raises:
        FileNotFoundError: If path does not exist.
        json.JSONDecodeError: If content is not valid JSON after all fallbacks.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f'safe_json_load: file not found: {path}')

    encodings_to_try = [encoding, 'utf-8-sig', 'latin-1']
    for enc in encodings_to_try:
        try:
            with open(path, encoding=enc) as f:
                return json.load(f)
        except (UnicodeDecodeError, UnicodeError):
            continue
        except json.JSONDecodeError:
            # Content decoded but wasn't valid JSON — no point trying other encodings
            raise

    # Final fallback: read bytes, replace bad chars, parse
    with open(path, 'rb') as f:
        raw = f.read().decode('utf-8', errors='replace')
    return json.loads(raw)


def safe_json_dump(obj: Any, path: str, indent: int = 2) -> None:
    """
    Save JSON ensuring the file is written as utf-8.

    Always writes utf-8 regardless of system locale — safe for data
    containing accented characters, CJK, etc.

    Args:
        obj:    JSON-serializable object.
        path:   Output file path.
        indent: JSON indentation level (default 2).
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)


# ── Convenience: list/str normalizer for Open Library fields ──────────────────

def to_str(value: Any, max_len: int = 0) -> str:
    """
    Normalize a field that may be a string, a list, or None.

    Open Library API returns author_name and sometimes title as lists.
    This handles both transparently.

    Example:
        to_str(['Plato', 'Trans. by John Smith'])  ->  'Plato'
        to_str('Atlantis: A Novel')                ->  'Atlantis: A Novel'
        to_str(None)                               ->  ''
    """
    if value is None:
        return ''
    if isinstance(value, list):
        value = value[0] if value else ''
    result = str(value)
    if max_len > 0:
        result = result[:max_len]
    return result


def safe_to_str(value: Any, max_len: int = 0) -> str:
    """
    Normalize + ASCII-sanitize in one call.
    Use for terminal display of list-or-string fields from external APIs.
    """
    return safe_str(to_str(value), max_len=max_len)
