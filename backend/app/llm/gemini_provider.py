from __future__ import annotations

import asyncio

import google.generativeai as genai

from app.core.errors import LLMProviderError
from app.llm.base import ChatMessage, LLMProvider
from app.schemas.llm import ModelInfo


import logging
log = logging.getLogger(__name__)

def _to_gemini_history(messages: list[ChatMessage]) -> tuple[str, list[dict]]:
    """Gemini takes system instruction separately and uses (user, model) roles."""
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
    name = "gemini"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=api_key)

    async def list_models(self) -> list[ModelInfo]:
        try:
            # google-generativeai's list_models is sync; offload it.
            raw = await asyncio.to_thread(lambda: list(genai.list_models()))
        except Exception as e:
            raise LLMProviderError(f"Gemini: {e}", hint="Check your API key.") from e

        models: list[ModelInfo] = []
        for m in raw:
            if "generateContent" not in (m.supported_generation_methods or []):
                continue
            # Names look like 'models/gemini-1.5-pro'; the API takes either form.
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
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        system_instruction, history = _to_gemini_history(messages)
        
        # Log the outgoing prompt (without API keys)
        log.info("Gemini Request [Model: %s]", model)
        if system_instruction:
            log.info("System Instruction: %s", system_instruction)
        for i, h in enumerate(history):
             log.info("Message %d [%s]: %s", i, h["role"], h["parts"][0])

        async def _call(sys_instr: str | None, hist: list[dict]) -> str:
            client = genai.GenerativeModel(
                model_name=model,
                system_instruction=sys_instr,
            )
            if not hist:
                raise LLMProviderError("No user message to send.", hint="Internal error.")
            last = hist[-1]
            chat = client.start_chat(history=hist[:-1])
            resp = await asyncio.to_thread(
                chat.send_message,
                last["parts"][0],
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            return (getattr(resp, "text", "") or "").strip()

        try:
            output = await _call(system_instruction or None, history)
        except Exception as e:
            # Gemma and some other models don't support system_instruction.
            # If we see that specific error, retry by prepending system instruction to the first user message.
            err_msg = str(e).lower()
            if "developer instruction is not enabled" in err_msg and system_instruction:
                log.warning("Model does not support system instructions; retrying with prepended prompt.")
                # Prepend system instruction to the very first user message in history
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

        log.info("Gemini Response: %s", output)
        return output
