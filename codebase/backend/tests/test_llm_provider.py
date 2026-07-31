"""Tests for the small provider adapter without external API calls."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.rag import llm_provider


def test_provider_dispatch(monkeypatch):
    monkeypatch.setattr(llm_provider.config, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(
        llm_provider,
        "_openai_text",
        lambda system, user: f"{system}|{user}",
    )

    assert llm_provider.generate_text("system", "user") == "system|user"


def test_unsupported_provider_is_rejected(monkeypatch):
    monkeypatch.setattr(llm_provider.config, "LLM_PROVIDER", "unknown")

    with pytest.raises(llm_provider.LLMProviderError, match="Unsupported"):
        llm_provider.generate_text("system", "user")


def test_openai_uses_responses_api(monkeypatch):
    calls = []
    fake_client = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **kwargs: calls.append(kwargs)
            or SimpleNamespace(output_text="grounded")
        )
    )
    monkeypatch.setattr(llm_provider, "_get_openai_client", lambda: fake_client)
    monkeypatch.setattr(llm_provider.config, "LLM_MODEL", "gpt-4o-mini")

    answer = llm_provider._openai_text("system", "user")

    assert answer == "grounded"
    assert calls[0]["instructions"] == "system"
    assert calls[0]["input"] == "user"
    assert "reasoning" not in calls[0]

    # Test reasoning model includes reasoning effort
    calls.clear()
    monkeypatch.setattr(llm_provider.config, "LLM_MODEL", "o1-mini")
    llm_provider._openai_text("system", "user")
    assert calls[0]["reasoning"] == {"effort": "low"}



def test_openrouter_uses_chat_completions(monkeypatch):
    calls = []
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: calls.append(kwargs)
                or SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content="grounded")
                        )
                    ]
                )
            )
        )
    )
    monkeypatch.setattr(llm_provider, "_get_openrouter_client", lambda: fake_client)
    monkeypatch.setattr(llm_provider.config, "LLM_MODEL", "test-model")

    answer = llm_provider._openrouter_text("system", "user")

    assert answer == "grounded"
    assert calls[0]["messages"][0] == {
        "role": "system",
        "content": "system",
    }


def test_gemini_uses_generate_content(monkeypatch):
    calls = []
    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: calls.append(kwargs)
            or SimpleNamespace(text="grounded")
        )
    )
    monkeypatch.setattr(llm_provider, "_get_gemini_client", lambda: fake_client)
    monkeypatch.setattr(llm_provider.config, "LLM_MODEL", "test-model")

    answer = llm_provider._gemini_text("system", "user")

    assert answer == "grounded"
    assert calls[0]["contents"] == "user"
    assert calls[0]["config"]["system_instruction"] == "system"


def test_provider_wraps_errors_without_secret_text(monkeypatch):
    monkeypatch.setattr(llm_provider.config, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(
        llm_provider,
        "_openai_text",
        lambda *args: (_ for _ in ()).throw(RuntimeError("secret-key-value")),
    )

    with pytest.raises(llm_provider.LLMProviderError) as exc_info:
        llm_provider.generate_text("system", "user")

    assert "secret-key-value" not in str(exc_info.value)
