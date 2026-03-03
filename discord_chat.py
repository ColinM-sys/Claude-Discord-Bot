#!/usr/bin/env python3
"""
Interactive Claude Agent + Discord Chat
Type questions, Claude answers, responses go to Discord

Usage:
    python discord_chat.py
"""

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
        "username": "Claude Agent",
        "embeds": [{
            "title": title or "Agent Response",
            "description": message[:4000],
            "color": 5814783
        }]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(DISCORD_WEBHOOK, json=payload, timeout=10.0)
        return response.status_code in [200, 204]


async def main():
    print("=" * 50)
    print("  Claude Agent + Discord Interactive Chat")
    print("=" * 50)
    print("Type your questions. Claude will answer and post to Discord.")
    print("Commands: 'quit' to exit, 'local' to skip Discord")
    print("=" * 50)
    print()

    send_to_discord_flag = True

    while True:
        try:
            question = input("You: ").strip()

            if not question:
                continue

            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if question.lower() == 'local':
                send_to_discord_flag = not send_to_discord_flag
                status = "ON" if send_to_discord_flag else "OFF"
                print(f"[Discord posting is now {status}]")
                continue

            print("Claude: ", end="", flush=True)

            # Get response from Claude
            answer = await ask_claude(question)
            print(answer)

            # Send to Discord if enabled
            if send_to_discord_flag:
                success = await send_to_discord(answer, f"Q: {question[:80]}")
                if success:
                    print("[Sent to Discord]")
                else:
                    print("[Discord send failed]")

            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
