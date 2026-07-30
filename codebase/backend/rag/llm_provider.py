"""Resident provider clients behind one text-generation interface."""
from __future__ import annotations

from functools import lru_cache

from backend import config


class LLMProviderError(RuntimeError):
    pass


def _require(value: str, name: str) -> str:
    if not value:
        raise LLMProviderError(f"Missing required configuration: {name}")
    return value


@lru_cache(maxsize=1)
def _get_openai_client():
    from openai import OpenAI

    return OpenAI(
        api_key=_require(config.OPENAI_API_KEY, "OPENAI_API_KEY"),
        timeout=config.LLM_TIMEOUT_SECONDS,
    )


@lru_cache(maxsize=1)
def _get_openrouter_client():
    from openai import OpenAI

    return OpenAI(
        api_key=_require(config.OPENROUTER_API_KEY, "OPENROUTER_API_KEY"),
        base_url=config.OPENROUTER_BASE_URL,
        timeout=config.LLM_TIMEOUT_SECONDS,
    )


@lru_cache(maxsize=1)
def _get_gemini_client():
    from google import genai

    return genai.Client(
        api_key=_require(config.GEMINI_API_KEY, "GEMINI_API_KEY")
    )


def _openai_text(system_prompt: str, user_prompt: str) -> str:
    response = _get_openai_client().responses.create(
        model=_require(config.LLM_MODEL, "LLM_MODEL"),
        instructions=system_prompt,
        input=user_prompt,
        max_output_tokens=config.LLM_MAX_OUTPUT_TOKENS,
        reasoning={"effort": "low"},
    )
    return response.output_text


def _openrouter_text(system_prompt: str, user_prompt: str) -> str:
    response = _get_openrouter_client().chat.completions.create(
        model=_require(config.LLM_MODEL, "LLM_MODEL"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=config.LLM_MAX_OUTPUT_TOKENS,
    )
    return response.choices[0].message.content or ""


def _gemini_text(system_prompt: str, user_prompt: str) -> str:
    response = _get_gemini_client().models.generate_content(
        model=_require(config.LLM_MODEL, "LLM_MODEL"),
        contents=user_prompt,
        config={
            "system_instruction": system_prompt,
            "max_output_tokens": config.LLM_MAX_OUTPUT_TOKENS,
        },
    )
    return response.text or ""


def generate_text(system_prompt: str, user_prompt: str) -> str:
    providers = {
        "openai": _openai_text,
        "openrouter": _openrouter_text,
        "gemini": _gemini_text,
    }
    provider = config.LLM_PROVIDER.casefold()
    generate = providers.get(provider)
    if generate is None:
        raise LLMProviderError(f"Unsupported LLM provider: {provider}")
    try:
        answer = generate(system_prompt, user_prompt).strip()
    except LLMProviderError:
        raise
    except Exception as exc:
        raise LLMProviderError(f"{provider} generation failed") from exc
    if not answer:
        raise LLMProviderError(f"{provider} returned an empty response")
    return answer
