"""Tests for provider routing and fail-safe nudge copy generation."""

import json
from dataclasses import replace

import httpx
import pytest

from backend.core.settings import settings
from backend.services.llm_provider import LLMProviderRouter


def _configured_settings():
    return replace(
        settings,
        groq_api_key="groq-test-key",
        gemini_api_key="gemini-test-key",
    )


def _groq_response(content: str = '{"provider": "groq"}') -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": content}}]},
    )


def _gemini_response(content: str = '{"provider": "gemini"}') -> httpx.Response:
    return httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": content}]}}]},
    )


@pytest.mark.asyncio
async def test_router_rotates_providers_after_success():
    requested_hosts = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_hosts.append(request.url.host)
        if request.url.host == "api.groq.com":
            assert request.headers["authorization"] == "Bearer groq-test-key"
            payload = json.loads(request.content)
            assert payload["model"] == "openai/gpt-oss-20b"
            assert payload["response_format"] == {"type": "json_object"}
            return _groq_response()
        assert request.headers["x-goog-api-key"] == "gemini-test-key"
        payload = json.loads(request.content)
        assert payload["generationConfig"]["responseMimeType"] == "application/json"
        return _gemini_response()

    router = LLMProviderRouter(
        _configured_settings(),
        transport=httpx.MockTransport(handler),
    )

    first = await router.generate_json("system", "prompt")
    second = await router.generate_json("system", "different prompt")

    assert first == {"provider": "groq"}
    assert second == {"provider": "gemini"}
    assert requested_hosts == ["api.groq.com", "generativelanguage.googleapis.com"]


@pytest.mark.asyncio
async def test_router_caches_successful_identical_requests():
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        assert request.method == "POST"
        request_count += 1
        return _groq_response()

    router = LLMProviderRouter(
        replace(_configured_settings(), gemini_api_key=""),
        transport=httpx.MockTransport(handler),
    )

    first = await router.generate_json("system", "same prompt")
    second = await router.generate_json("system", "same prompt")

    assert first == second == {"provider": "groq"}
    assert request_count == 1


@pytest.mark.asyncio
async def test_router_fails_over_on_provider_rate_limit():
    requested_hosts = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_hosts.append(request.url.host)
        if request.url.host == "api.groq.com":
            return httpx.Response(429, headers={"Retry-After": "30"})
        return _gemini_response()

    router = LLMProviderRouter(
        _configured_settings(),
        transport=httpx.MockTransport(handler),
    )

    result = await router.generate_json("system", "prompt")

    assert result == {"provider": "gemini"}
    assert requested_hosts == ["api.groq.com", "generativelanguage.googleapis.com"]


@pytest.mark.asyncio
async def test_router_returns_none_when_all_providers_fail():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(503)

    router = LLMProviderRouter(
        _configured_settings(),
        transport=httpx.MockTransport(handler),
    )

    assert await router.generate_json("system", "prompt") is None


@pytest.mark.asyncio
async def test_nudge_copy_is_cached_and_customer_data_stays_local(monkeypatch):
    from backend.agents import nudge_agent

    class FakeRouter:
        def __init__(self):
            self.prompts = []

        async def generate_json(self, system_prompt, user_prompt, **kwargs):
            assert "JSON" in system_prompt
            assert kwargs["max_tokens"] == 256
            self.prompts.append(user_prompt)
            return {
                "subject": "Supply update",
                "body": "A suitable alternative is available.",
                "cta_text": "View alternative",
            }

    fake_router = FakeRouter()
    monkeypatch.setattr(nudge_agent, "llm_router", fake_router)
    state = nudge_agent.NudgeState(
        at_risk_sku_ids=["SKU-1"],
        at_risk_skus=[{"sku_id": "SKU-1", "name": "Product One"}],
        affected_customers=[
            {
                "name": "Alice",
                "email": "alice@example.test",
                "purchase_history": [
                    {"sku_id": "SKU-1", "date": "2025-01-02"}
                ],
            },
            {
                "name": "Bob",
                "email": "bob@example.test",
                "purchase_history": [
                    {"sku_id": "SKU-1", "date": "2025-01-03"}
                ],
            },
        ],
        substitutes={
            "SKU-1": [
                {
                    "sku_id": "SKU-2",
                    "name": "Product Two",
                    "current_stock": 12,
                }
            ]
        },
    )

    result = await nudge_agent.generate_offer_copy(state)

    assert len(fake_router.prompts) == 1
    assert all(
        value not in fake_router.prompts[0]
        for value in ("Alice", "Bob", "alice@example.test", "2025-01-02")
    )
    assert [offer["customer_name"] for offer in result.offer_copies] == [
        "Alice",
        "Bob",
    ]
    assert all(offer["body"].startswith("Hi ") for offer in result.offer_copies)


@pytest.mark.asyncio
async def test_nudge_copy_uses_local_template_when_provider_fails(monkeypatch):
    from backend.agents import nudge_agent

    class FailedRouter:
        async def generate_json(self, system_prompt, user_prompt, **kwargs):
            assert system_prompt and user_prompt
            assert kwargs["max_tokens"] == 256
            return None

    monkeypatch.setattr(nudge_agent, "llm_router", FailedRouter())
    state = nudge_agent.NudgeState(
        at_risk_sku_ids=["SKU-1"],
        at_risk_skus=[{"sku_id": "SKU-1", "name": "Product One"}],
        affected_customers=[
            {
                "name": "Alice",
                "purchase_history": [{"sku_id": "SKU-1"}],
            }
        ],
        substitutes={
            "SKU-1": [{"sku_id": "SKU-2", "name": "Product Two"}]
        },
    )

    result = await nudge_agent.generate_offer_copy(state)

    assert len(result.offer_copies) == 1
    assert "Product Two is an available alternative." in result.offer_copies[0]["body"]


@pytest.mark.asyncio
async def test_risk_response_is_bounded_and_drops_untrusted_score(monkeypatch):
    from backend.agents import disruption_agent

    class FakeRouter:
        async def generate_json(self, system_prompt, user_prompt, **kwargs):
            assert "supply-chain risk" in system_prompt
            assert user_prompt
            assert kwargs["temperature"] == 0.1
            return {
                "analyses": [
                    {
                        "affected_sku_ids": ["SKU-1", "SKU-1"],
                        "risk_delta": 1000,
                        "target_score": 10000,
                        "reasoning": "A test signal",
                    }
                ]
            }

    monkeypatch.setattr(disruption_agent, "llm_router", FakeRouter())

    result = await disruption_agent._call_llm("test signal")

    assert result == {
        "analyses": [
            {
                "affected_sku_ids": ["SKU-1"],
                "risk_delta": 100,
                "reasoning": "A test signal",
            }
        ]
    }
