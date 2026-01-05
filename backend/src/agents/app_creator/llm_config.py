"""LLM configuration for app_creator agent."""
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from src.config import settings


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7
):
    """
    Get LLM instance based on configuration.

    Args:
        provider: LLM provider (openai, anthropic). Defaults to settings.llm_provider
        model: Model name. Defaults to settings.llm_model
        temperature: Sampling temperature

    Returns:
        LLM instance
    """
    provider = provider or settings.llm_provider

    # 确定使用的模型：优先使用传入的 model 参数，其次使用 provider 专用模型，最后使用默认模型
    if provider == "openai":
        model = model or settings.openai_model or settings.llm_model
    elif provider == "anthropic":
        model = model or settings.anthropic_model or settings.llm_model
    else:
        model = model or settings.llm_model

    if provider == "openai":
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError(
                "OpenAI API key not configured. "
                "Please set OPENAI_API_KEY in your .env file."
            )

        llm_kwargs = {
            "model": model,
            "temperature": temperature,
            "api_key": api_key
        }

        # 支持自定义 base_url（可选）
        if settings.openai_base_url:
            llm_kwargs["base_url"] = settings.openai_base_url

        return ChatOpenAI(**llm_kwargs)

    elif provider == "anthropic":
        api_key = settings.anthropic_api_key
        if not api_key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Please set ANTHROPIC_API_KEY in your .env file."
            )

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=api_key
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
