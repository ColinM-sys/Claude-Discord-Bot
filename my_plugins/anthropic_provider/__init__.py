# Custom Anthropic/Claude LLM Provider for NeMo Agent Toolkit
#
# To use: pip install anthropic
# Set environment variable: ANTHROPIC_API_KEY=your_key
#
# In your workflow YAML:
# llms:
#   claude:
#     _type: anthropic_claude
#     model_name: claude-sonnet-4-20250514

import os
from typing import AsyncIterator

from pydantic import Field
from anthropic import AsyncAnthropic

from nat.llm.llm_provider import LLMProviderConfig, register_llm_provider
from nat.data_classes import LLMMessage


@register_llm_provider(name="anthropic_claude")
class AnthropicClaudeConfig(LLMProviderConfig):
    """Anthropic Claude LLM provider."""

    model_name: str = Field(
        default="claude-sonnet-4-20250514",
        description="The Anthropic model to use"
    )
    temperature: float = Field(default=0.0, description="Sampling temperature")
    max_tokens: int = Field(default=4096, description="Maximum tokens in response")
    api_key: str | None = Field(default=None, description="Anthropic API key (or use ANTHROPIC_API_KEY env var)")

    async def create_client(self):
        """Create the Anthropic client."""
        api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return AsyncAnthropic(api_key=api_key)

    async def generate(self, messages: list[LLMMessage], **kwargs) -> str:
        """Generate a response from Claude."""
        client = await self.create_client()

        # Convert messages to Anthropic format
        anthropic_messages = []
        system_prompt = None

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        response = await client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt or "",
            messages=anthropic_messages
        )

        return response.content[0].text

    async def generate_stream(self, messages: list[LLMMessage], **kwargs) -> AsyncIterator[str]:
        """Stream a response from Claude."""
        client = await self.create_client()

        anthropic_messages = []
        system_prompt = None

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        async with client.messages.stream(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt or "",
            messages=anthropic_messages
        ) as stream:
            async for text in stream.text_stream:
                yield text
