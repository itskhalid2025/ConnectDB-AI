# ================================================================
# FILE: llm_utils.py
# PATH: backend/app/utils/llm_utils.py
# ================================================================
# DESCRIPTION:
#   Utility functions for robust LLM response handling.
#   Includes:
#   - JSON extraction from mixed text/markdown
#   - SQL cleaning and fence removal
#   - Truncation-aware response repairs
#
# CREATED: 2026-05-08 | 01:30 AM
#
# EDIT LOG:
# ----------------------------------------------------------------
# [2026-05-08 | 01:30 AM] - Initial file created. Added 
#                           extract_json() and clean_sql().
# ================================================================

import json
import logging
import re

log = logging.getLogger(__name__)

def extract_json(text: str) -> dict:
    """
    Robustly extracts a JSON object from a string, even if it contains 
    markdown fences, prose, or is slightly malformed/truncated.
    
    Args:
        text: The raw text from the LLM.
        
    Returns:
        The parsed dictionary.
        
    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    if not text:
        raise ValueError("Empty response from LLM")

    # 1. Try direct parse first
    clean = text.strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # 2. Look for markdown fences
    match = re.search(r"```json\s*(.*?)\s*(?:```|$)", clean, re.DOTALL)
    if match:
        content = match.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If still failing, try to fix truncation below
            clean = content

    # 3. Find first { and last }
    start = clean.find("{")
    end = clean.rfind("}")
    
    if start != -1:
        if end != -1 and end > start:
            # Potentially complete JSON
            json_str = clean[start : end + 1]
        else:
            # Truncated JSON starting with {
            json_str = clean[start:]
            # Attempt a naive fix: add missing braces if it looks like it's just missing them
            # This is risky but better than failing if it's just a simple dict
            if not json_str.endswith("}"):
                json_str += "}"
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            log.warning("Final JSON extraction attempt failed: %s. String was: %s", e, json_str)
            raise ValueError(f"Could not parse extracted JSON: {e}")

    raise ValueError("No JSON object found in text")

def clean_sql(sql: str) -> str:
    """
    Cleans raw SQL output from LLM, stripping fences and handling 
    truncation artifacts.
    
    Args:
        sql: The raw SQL string.
        
    Returns:
        Cleaned SQL string.
    """
    s = sql.strip()
    
    # Remove markdown fences (even if unterminated)
    if s.startswith("```"):
        # Split by first newline to skip ```sql
        lines = s.split("\n", 1)
        if len(lines) > 1:
            s = lines[1]
        else:
            # Just ``` on one line
            s = s.lstrip("`").replace("sql", "", 1).strip()
            
    # Remove any trailing fence if it exists
    if s.endswith("```"):
        s = s[:-3]
    
    # Remove trailing semicolons (we add our own/handle them)
    s = s.strip().rstrip(";")
    
    return s.strip()
