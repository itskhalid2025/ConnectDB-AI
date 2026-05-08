"""
File: query_classifier.py
Version: 1.0.0
Created At: 2026-04-29
Description: Stage 1 Pipeline Service. Classifies user intent and evaluates 
             question clarity using the LLM.
"""

import json
import logging
from typing import TypedDict

from app.llm.base import LLMProvider
from app.llm.prompts import build_classifier_messages
from app.schemas.llm import AIConfig
from app.utils.llm_utils import extract_json

log = logging.getLogger(__name__)

class ClassificationResult(TypedDict):
    strategy: str
    clarity_score: float
    reason: str

async def classify_query(
    provider: LLMProvider,
    model: str,
    question: str,
    schema_text: str
) -> ClassificationResult:
    """
    Calls the LLM to classify the user's natural language query.
    """
    messages = build_classifier_messages(question, schema_text)
    
    raw_response = await provider.chat(
        model=model,
        messages=messages,
        max_tokens=400, # Increased to allow for reasoning
        temperature=0.0,
        response_format="json"
    )
    
    try:
        result = extract_json(raw_response)
        return {
            "strategy": result.get("strategy", "general"),
            "clarity_score": float(result.get("clarity_score", 1.0)),
            "reason": result.get("reason", "")
        }
    except (json.JSONDecodeError, ValueError) as e:
        log.error("Failed to parse classification JSON: %s. Raw: %s", e, raw_response)
        return {
            "strategy": "general",
            "clarity_score": 1.0,
            "reason": "Fallback due to classification error"
        }
