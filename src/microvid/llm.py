from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

from .runtime_config import load_local_runtime_environment


class LLMError(RuntimeError):
    """Raised when an LLM provider cannot produce a usable response."""


class JSONLLMProvider(Protocol):
    provider_name: str
    model: str

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...


def _gemini_compatible_schema(value: Any) -> Any:
    """Remove array bounds rejected by Gemini's structured-output endpoint.

    The lesson builders still enforce their slide/video cardinality locally;
    this only adapts the schema sent to the provider.
    """
    if isinstance(value, dict):
        return {
            key: _gemini_compatible_schema(item)
            for key, item in value.items()
            if key not in {"minItems", "maxItems"}
        }
    if isinstance(value, list):
        return [_gemini_compatible_schema(item) for item in value]
    return value


def _is_transient_provider_error(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code in {408, 429, 500, 502, 503, 504}:
        return True
    return type(exc).__name__ in {
        "ConnectError",
        "ConnectTimeout",
        "ReadError",
        "ReadTimeout",
        "RemoteProtocolError",
        "ServerError",
        "WriteError",
        "WriteTimeout",
    }


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
        load_local_runtime_environment()
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise LLMError(
                f"Gemini is the default content generator, but {self.api_key_env} is not set. "
                f"Set that environment variable or explicitly use --generator deterministic "
                f"for an offline/debug draft."
            )
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except ImportError as exc:
            raise LLMError(
                "The google-genai package is required for Gemini generation. "
                "Install the project dependencies before running the LLM pipeline."
            ) from exc
        return genai.Client(api_key=api_key), types

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        client, types = self._client()
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=_gemini_compatible_schema(schema),
            thinking_config=types.ThinkingConfig(
                thinking_level=self.thinking_level.upper()
            ),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )
        text = ""
        for attempt in range(3):
            try:
                chunks = client.models.generate_content_stream(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                text = "".join(chunk.text or "" for chunk in chunks)
                break
            except Exception as exc:
                if attempt == 2 or not _is_transient_provider_error(exc):
                    raise LLMError(
                        f"Gemini generation failed for model {self.model}: {exc}"
                    ) from exc
                time.sleep(2**attempt)

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
