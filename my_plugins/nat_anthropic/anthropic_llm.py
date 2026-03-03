# SPDX-FileCopyrightText: Copyright (c) 2025
# SPDX-License-Identifier: Apache-2.0
#
# Custom Anthropic Claude LLM Provider for NeMo Agent Toolkit
#
# Usage:
#   1. pip install anthropic
#   2. Set ANTHROPIC_API_KEY environment variable
#   3. pip install -e my_plugins/nat_anthropic
#   4. Use in YAML:
#      llms:
#        claude:
#          _type: anthropic
#          model_name: claude-sonnet-4-20250514

from pydantic import ConfigDict, Field

from nat.builder.builder import Builder
from nat.builder.llm import LLMProviderInfo
from nat.cli.register_workflow import register_llm_provider
from nat.data_models.llm import LLMBaseConfig
from nat.data_models.retry_mixin import RetryMixin
from nat.data_models.temperature_mixin import TemperatureMixin
from nat.data_models.top_p_mixin import TopPMixin


class AnthropicModelConfig(LLMBaseConfig, RetryMixin, TemperatureMixin, TopPMixin, name="anthropic"):
    """An Anthropic Claude LLM provider to be used with an LLM client."""

    model_config = ConfigDict(protected_namespaces=(), extra="allow")

    api_key: str | None = Field(
        default=None,
        description="Anthropic API key. Falls back to ANTHROPIC_API_KEY env var."
    )
    model_name: str = Field(
        default="claude-sonnet-4-20250514",
        description="The Anthropic model name (e.g., claude-sonnet-4-20250514, claude-3-5-sonnet-20241022)"
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum number of tokens to generate."
    )
    max_retries: int = Field(
        default=3,
        description="The max number of retries for the request."
    )


@register_llm_provider(config_type=AnthropicModelConfig)
async def anthropic_llm(config: AnthropicModelConfig, _builder: Builder):
    """Create an Anthropic Claude LLM provider."""
    yield LLMProviderInfo(config=config, description="An Anthropic Claude model for use with an LLM client.")
