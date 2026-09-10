from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol


class LLMError(RuntimeError):
    """Raised when an LLM provider cannot produce a usable response."""


class JSONLLMProvider(Protocol):
    provider_name: str
    model: str

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class GeminiProvider:
    """Google Gemini structured-output provider using the official google-genai SDK.

    The model name is deliberately constructor/config data rather than a Python constant in
    the lesson engine. The packaged profile defaults to Google's moving Flash-latest alias.
    """

    model: str = "gemini-flash-latest"
    thinking_level: str = "high"
    api_key_env: str = "GEMINI_API_KEY"
    provider_name: str = "gemini"

    def _client(self):
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise LLMError(
                f"Gemini is the default content generator, but {self.api_key_env} is not set. "
                f"Set that environment variable or explicitly use --generator deterministic "
                f"for an offline/debug draft."
            )
        try:
            from google import genai  # type: ignore
        except ImportError as exc:
            raise LLMError(
                "The google-genai package is required for Gemini generation. "
                "Install the project dependencies before running the LLM pipeline."
            ) from exc
        return genai.Client(api_key=api_key)

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        client = self._client()
        try:
            interaction = client.interactions.create(
                model=self.model,
                input=prompt,
                generation_config={"thinking_level": self.thinking_level},
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": schema,
                },
            )
            text = interaction.output_text
        except Exception as exc:
            raise LLMError(
                f"Gemini generation failed for model {self.model}: {exc}"
            ) from exc

        if not text:
            raise LLMError(f"Gemini model {self.model} returned an empty response.")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError("Gemini returned invalid JSON despite structured-output mode.") from exc
        if not isinstance(payload, dict):
            raise LLMError("Gemini structured output must be a JSON object.")
        return payload


def provider_from_config(config: dict[str, Any] | None, *, model: str | None = None, thinking_level: str | None = None) -> JSONLLMProvider:
    cfg = config or {}
    provider = str(cfg.get("provider", "gemini")).casefold()
    if provider != "gemini":
        raise LLMError(
            f"Unsupported LLM provider '{provider}'. v0.3 ships Gemini as the default provider; "
            "the interface is intentionally provider-pluggable for future adapters."
        )
    return GeminiProvider(
        model=model or str(cfg.get("model", "gemini-flash-latest")),
        thinking_level=thinking_level or str(cfg.get("thinking_level", "high")),
        api_key_env=str(cfg.get("api_key_env", "GEMINI_API_KEY")),
    )
