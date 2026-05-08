"""
File: gemini_provider.py
Version: 1.1.0
Created At: 2026-04-25
Updated At: 2026-04-29
Description: Google Gemini LLM provider implementation. Handles communication with Google's 
             Generative AI API, including history conversion and system instruction fallback logic.
"""

from __future__ import annotations

import asyncio
import logging
import google.generativeai as genai

from app.core.errors import LLMProviderError
from app.llm.base import ChatMessage, LLMProvider
from app.schemas.llm import ModelInfo

# Initialize logger
log = logging.getLogger(__name__)


def _to_gemini_history(messages: list[ChatMessage]) -> tuple[str, list[dict]]:
    """
    Translates standard ChatMessage objects into the format expected by Google's API.
    Gemini takes 'system_instruction' separately and uses ('user', 'model') roles for history.
    
    Args:
        messages: List of ChatMessage objects.
        
    Returns:
        A tuple of (concatenated_system_instructions, list_of_chat_history_dicts).
    """
    system_parts: list[str] = []
    chat_history: list[dict] = []
    for m in messages:
        if m.role == "system":
            system_parts.append(m.content)
        elif m.role == "user":
            chat_history.append({"role": "user", "parts": [m.content]})
        elif m.role == "assistant":
            chat_history.append({"role": "model", "parts": [m.content]})
    return "\n\n".join(system_parts), chat_history


class GeminiProvider(LLMProvider):
    """
    Provider class for Google Gemini models.
    """
    name = "gemini"

    def __init__(self, api_key: str):
        """Initialize the Google GenerativeAI client with the provided API key."""
        super().__init__(api_key)
        genai.configure(api_key=api_key)

    async def list_models(self) -> list[ModelInfo]:
        """
        Fetch available models from the Google API that support content generation.
        
        Returns:
            List of ModelInfo objects containing model IDs and labels.
        """
        try:
            # list_models is a blocking call; offload to a background thread.
            raw = await asyncio.to_thread(lambda: list(genai.list_models()))
        except Exception as e:
            raise LLMProviderError(f"Gemini: {e}", hint="Check your API key.") from e

        models: list[ModelInfo] = []
        for m in raw:
            if "generateContent" not in (m.supported_generation_methods or []):
                continue
            mid = m.name.replace("models/", "")
            label = m.display_name or mid
            models.append(ModelInfo(id=mid, label=label))
        models.sort(key=lambda m: m.id)
        return models

    async def chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 1500,
        temperature: float = 0.0,
    ) -> str:
        """
        Send a chat completion request to Gemini.
        
        This method includes specialized logging and a fallback mechanism for models 
        (like Gemma) that do not support 'system_instruction'.
        """
        system_instruction, history = _to_gemini_history(messages)
        
        # Log outgoing prompt metadata for debugging
        log.info("Gemini Request [Model: %s]", model)
        if system_instruction:
            log.info("System Instruction: %s", system_instruction)
        for i, h in enumerate(history):
             log.info("Message %d [%s]: %s", i, h["role"], h["parts"][0])

        async def _call(sys_instr: str | None, hist: list[dict]) -> str:
            """Internal wrapper to execute the Gemini API call."""
            client = genai.GenerativeModel(
                model_name=model,
                system_instruction=sys_instr,
            )
            if not hist:
                raise LLMProviderError("No user message to send.", hint="Internal error.")
            
            last = hist[-1]
            chat = client.start_chat(history=hist[:-1])
            
            # Avoid strict 0.0 temperature on experimental models to prevent early stops
            safe_temp = max(0.05, temperature)
            
            resp = await chat.send_message_async(
                last["parts"][0],
                generation_config={
                    "temperature": safe_temp,
                    # Deliberately omitting max_output_tokens due to Gemini 2.5 flash early-truncation bugs
                },
            )
            try:
                finish_reason = resp.candidates[0].finish_reason
                log.info("Gemini Finish Reason: %s", finish_reason)
            except Exception as e:
                pass
            return (getattr(resp, "text", "") or "").strip()

        try:
            output = await _call(system_instruction or None, history)
        except Exception as e:
            # Handle models lacking 'system_instruction' support (e.g., Gemma)
            err_msg = str(e).lower()
            if "developer instruction is not enabled" in err_msg and system_instruction:
                log.warning("Model does not support system instructions; retrying with prepended prompt.")
                
                # Logic: Prepend system instructions to the first available user message
                new_history = history.copy()
                if new_history and new_history[0]["role"] == "user":
                    new_history[0] = {
                        "role": "user",
                        "parts": [f"{system_instruction}\n\n{new_history[0]['parts'][0]}"]
                    }
                else:
                    new_history.insert(0, {"role": "user", "parts": [system_instruction]})
                
                try:
                    output = await _call(None, new_history)
                except Exception as inner_e:
                    raise LLMProviderError(f"Gemini (Retry): {inner_e}") from inner_e
            else:
                raise LLMProviderError(f"Gemini: {e}", hint="Check the API key and selected model.") from e

        # Log final output
        log.info("Gemini Response: %s", output)
        return output
