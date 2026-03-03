"""
Bridge Watcher - Monitors incoming.txt and auto-responds via Claude API
Runs continuously in background to provide fast Discord responses
"""
import os
import json
import time
import anthropic
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
BRIDGE_DIR = PROJECT_ROOT / "bridge"
INCOMING_FILE = BRIDGE_DIR / "incoming.txt"
OUTGOING_FILE = BRIDGE_DIR / "outgoing.txt"
SEEN_FILE = BRIDGE_DIR / "watcher_seen.txt"

# Initialize Claude client
client = anthropic.Anthropic()

def load_seen_timestamps():
    """Load timestamps we've already processed."""
    if not SEEN_FILE.exists():
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen_timestamp(timestamp):
    """Mark a timestamp as seen."""
    with open(SEEN_FILE, "a") as f:
        f.write(timestamp + "\n")

def get_new_messages():
    """Get messages we haven't processed yet."""
    if not INCOMING_FILE.exists():
        return []

    seen = load_seen_timestamps()
    new_messages = []

    with open(INCOMING_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                ts = msg.get("timestamp", "")
                if ts and ts not in seen:
                    # Skip SYSTEM messages
                    if msg.get("user") != "SYSTEM":
                        new_messages.append(msg)
            except json.JSONDecodeError:
                continue

    return new_messages

def send_response(channel_id, content):
    """Write response to outgoing file for Discord bot to pick up."""
    response = {
        "channel_id": channel_id,
        "content": content
    }
    with open(OUTGOING_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(response))
    print(f"[WATCHER] Sent response to channel {channel_id}")

def generate_response(message_content, user):
    """Generate a response using Claude API."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="""You are a helpful assistant responding to Discord messages.
Keep responses concise and friendly. You're connected to a Windows PC and Jetson Orin Nano.
The Jetson has 8GB RAM, runs Ubuntu 24.04, IP 10.0.0.195.
You can help with coding, system info, and general questions.""",
            messages=[
                {"role": "user", "content": f"{user} says: {message_content}"}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating response: {e}"

def main():
    print("[WATCHER] Bridge watcher started - monitoring for Discord messages...")

    while True:
        try:
            new_messages = get_new_messages()

            for msg in new_messages:
                ts = msg.get("timestamp", "")
                user = msg.get("user", "Unknown")
                content = msg.get("content", "")
                channel_id = msg.get("channel_id")

                if not channel_id or not content:
                    save_seen_timestamp(ts)
                    continue

                print(f"[WATCHER] New message from {user}: {content[:50]}...")

                # Generate and send response
                response = generate_response(content, user)
                send_response(channel_id, response)

                # Mark as processed
                save_seen_timestamp(ts)

            time.sleep(2)  # Check every 2 seconds

        except KeyboardInterrupt:
            print("[WATCHER] Shutting down...")
            break
        except Exception as e:
            print(f"[WATCHER] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
