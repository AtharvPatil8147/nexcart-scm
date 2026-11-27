"""Fail-safe JSON generation using Groq and Gemini with round-robin routing."""

import copy
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import quote

import httpx

from backend.core.settings import Settings, settings
from backend.utils.logger import get_logger

logger = get_logger("llm_provider")


@dataclass(frozen=True)
class _Provider:
    name: str
    api_key: str
    model_id: str


class LLMProviderRouter:
    """Try configured providers in a rotating order and return JSON or ``None``."""

    _CACHE_TTL_SECONDS = 300
    _MAX_CACHE_ENTRIES = 256

    def __init__(
        self,
        runtime_settings: Settings = settings,
        transport: Optional[httpx.AsyncBaseTransport] = None,
        timeout_seconds: float = 6.0,
    ) -> None:
        self._settings = runtime_settings
        self._transport = transport
        self._timeout_seconds = timeout_seconds
        self._next_provider_index = 0
        self._cooldowns: dict[str, float] = {}
        self._response_cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def _configured_providers(self) -> list[_Provider]:
        providers = []
        if self._settings.groq_api_key:
            providers.append(
                _Provider(
                    "groq",
                    self._settings.groq_api_key,
                    self._settings.groq_model_id,
                )
            )
        if self._settings.gemini_api_key:
            providers.append(
                _Provider(
                    "gemini",
                    self._settings.gemini_api_key,
                    self._settings.gemini_model_id,
                )
            )
        return providers

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Optional[dict[str, Any]]:
        """Generate a JSON object; return ``None`` if providers are unavailable."""
        cache_key = self._cache_key(
            system_prompt,
            user_prompt,
            temperature,
            max_tokens,
        )
        cached = self._response_cache.get(cache_key)
        if cached is not None:
            expires_at, result = cached
            if expires_at > time.monotonic():
                logger.debug("Returning cached LLM response")
                return copy.deepcopy(result)
            self._response_cache.pop(cache_key, None)

        providers = self._configured_providers()
        if not providers:
            logger.info("No LLM API keys configured; using application fallback")
            return None

        start = self._next_provider_index % len(providers)
        ordered = providers[start:] + providers[:start]
        self._next_provider_index = (start + 1) % len(providers)
        now = time.monotonic()

        for provider in ordered:
            if self._cooldowns.get(provider.name, 0) > now:
                logger.info("Skipping %s during its cooldown", provider.name)
                continue

            try:
                content = await self._request_provider(
                    provider,
                    system_prompt,
                    user_prompt,
                    temperature,
                    max_tokens,
                )
                result = self._parse_json(content)
                if isinstance(result, dict):
                    self._cache_response(cache_key, result)
                    return copy.deepcopy(result)
                logger.warning("%s returned a non-object JSON response", provider.name)
                self._cooldowns[provider.name] = time.monotonic() + 15
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                cooldown = self._cooldown_for_response(exc.response)
                self._cooldowns[provider.name] = time.monotonic() + cooldown
                logger.warning(
                    "%s request failed with HTTP %s; trying another provider",
                    provider.name,
                    status,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                self._cooldowns[provider.name] = time.monotonic() + 15
                logger.warning(
                    "%s request failed (%s); trying another provider",
                    provider.name,
                    type(exc).__name__,
                )
            except (ValueError, KeyError, TypeError) as exc:
                self._cooldowns[provider.name] = time.monotonic() + 15
                logger.warning(
                    "%s response could not be parsed (%s); trying another provider",
                    provider.name,
                    type(exc).__name__,
                )
            except Exception:
                self._cooldowns[provider.name] = time.monotonic() + 15
                logger.exception(
                    "%s unexpected provider error; trying another provider",
                    provider.name,
                )

        logger.warning("All configured LLM providers failed or are cooling down")
        return None

    @staticmethod
    def _cache_key(
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        cache_input = json.dumps(
            [system_prompt, user_prompt, temperature, max_tokens],
            ensure_ascii=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(cache_input.encode("utf-8")).hexdigest()

    def _cache_response(
        self,
        cache_key: str,
        result: dict[str, Any],
    ) -> None:
        if len(self._response_cache) >= self._MAX_CACHE_ENTRIES:
            oldest_key = next(iter(self._response_cache))
            self._response_cache.pop(oldest_key)
        self._response_cache[cache_key] = (
            time.monotonic() + self._CACHE_TTL_SECONDS,
            copy.deepcopy(result),
        )

    @staticmethod
    def _cooldown_for_response(response: httpx.Response) -> int:
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after", "")
            try:
                return min(300, max(1, int(float(retry_after))))
            except (ValueError, OverflowError):
                return 60
        return 15 if response.status_code >= 500 else 120

    async def _request_provider(
        self,
        provider: _Provider,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        if provider.name == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {provider.api_key}"}
            payload = {
                "model": provider.model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
        else:
            model_id = quote(provider.model_id, safe=".-_")
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_id}:generateContent"
            )
            headers = {"x-goog-api-key": provider.api_key}
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json",
                },
            }

        async with httpx.AsyncClient(
            transport=self._transport,
            timeout=self._timeout_seconds,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()

        if provider.name == "groq":
            return body["choices"][0]["message"]["content"]

        parts = body["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts)

    @staticmethod
    def _parse_json(content: str) -> Any:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return json.loads(text)


llm_router = LLMProviderRouter()
