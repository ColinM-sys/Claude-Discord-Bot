#!/usr/bin/env python3
"""
NeMo Agent Toolkit + Discord Bot
Asks Claude questions and sends responses to Discord

Usage:
    python discord_bot.py "What is 25 * 17?"
    python discord_bot.py "What time is it?"
"""

import sys
import asyncio
import os
import httpx

# Discord webhook URL
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")

# Anthropic API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


async def ask_claude(question: str) -> str:
    """Ask Claude a question and get a response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": question}]
            },
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"]
        else:
            return f"Error: {response.status_code} - {response.text}"


async def send_to_discord(message: str, title: str = None) -> bool:
    """Send a message to Discord."""
    payload = {
        "username": "NeMo Agent",
        "embeds": [{
            "title": title or "🤖 Agent Response",
            "description": message[:4000],  # Discord limit
            "color": 5814783  # Blue
        }]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(DISCORD_WEBHOOK, json=payload, timeout=10.0)
        return response.status_code in [200, 204]


async def main():
    if len(sys.argv) < 2:
        print("Usage: python discord_bot.py \"Your question here\"")
        print("\nExamples:")
        print("  python discord_bot.py \"What is 100 divided by 4?\"")
        print("  python discord_bot.py \"Write a haiku about coding\"")
        print("  python discord_bot.py \"Explain quantum computing in simple terms\"")
        return

    question = " ".join(sys.argv[1:])

    print(f"Question: {question}")
    print("Asking Claude...")

    # Get response from Claude
    answer = await ask_claude(question)
    print(f"Claude: {answer[:200]}..." if len(answer) > 200 else f"Claude: {answer}")

    # Send to Discord
    print("Sending to Discord...")
    success = await send_to_discord(answer, f"Q: {question[:100]}")

    if success:
        print("SUCCESS - Message sent to Discord!")
    else:
        print("FAILED to send to Discord")


if __name__ == "__main__":
    asyncio.run(main())
