#!/usr/bin/env python3
"""
Claude Bridge Bot
Bridges Discord messages to Claude Code via files

Messages from Discord -> bridge/incoming.txt
Responses from Claude Code <- bridge/outgoing.txt
"""

import discord
from discord.ext import commands, tasks
import asyncio
import os
import json
from datetime import datetime

# Configuration
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

# Bridge files
BRIDGE_DIR = os.path.join(os.path.dirname(__file__), "bridge")
INCOMING_FILE = os.path.join(BRIDGE_DIR, "incoming.txt")
OUTGOING_FILE = os.path.join(BRIDGE_DIR, "outgoing.txt")

# Ensure bridge directory exists
os.makedirs(BRIDGE_DIR, exist_ok=True)

# Store pending responses
pending_responses = {}  # message_id -> (channel, author)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


def write_incoming(user: str, user_id: int, channel_id: int, message_id: int, content: str):
    """Write incoming message to file for Claude Code to read."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "user_id": user_id,
        "channel_id": channel_id,
        "message_id": message_id,
        "content": content
    }
    with open(INCOMING_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")
    print(f"[INCOMING] {user}: {content[:50]}...")


def read_outgoing():
    """Read and clear outgoing responses from Claude Code."""
    if not os.path.exists(OUTGOING_FILE):
        return []

    with open(OUTGOING_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    # Clear the file
    with open(OUTGOING_FILE, "w", encoding="utf-8") as f:
        f.write("")

    responses = []
    for line in content.split("\n"):
        if line.strip():
            try:
                responses.append(json.loads(line))
            except json.JSONDecodeError:
                # Plain text response - send to most recent channel
                responses.append({"content": line})

    return responses


@bot.event
async def on_ready():
    print("=" * 50)
    print("  Claude Bridge Bot is online!")
    print("=" * 50)
    print(f"  Logged in as: {bot.user.name}")
    print(f"  Bridge directory: {BRIDGE_DIR}")
    print("=" * 50)
    print("  Messages will be written to: incoming.txt")
    print("  Responses read from: outgoing.txt")
    print("=" * 50)

    # Start checking for outgoing messages
    check_outgoing.start()


@tasks.loop(seconds=1)
async def check_outgoing():
    """Check for outgoing responses every second."""
    responses = read_outgoing()

    for resp in responses:
        content = resp.get("content", "")
        channel_id = resp.get("channel_id")

        if not content:
            continue

        # Try to find the channel
        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(content[:2000])
                print(f"[SENT] To channel {channel_id}: {content[:50]}...")
        else:
            # Send to the most recent pending channel
            if pending_responses:
                msg_id = list(pending_responses.keys())[-1]
                channel, author = pending_responses[msg_id]
                await channel.send(f"{author.mention} {content[:1900]}")
                print(f"[SENT] Reply: {content[:50]}...")


@bot.command(name="bridge")
async def bridge_command(ctx, *, message: str = None):
    """Send a message through the bridge to Claude Code."""
    if not message:
        await ctx.send("Usage: `!bridge <your message>`")
        return

    write_incoming(
        user=ctx.author.display_name,
        user_id=ctx.author.id,
        channel_id=ctx.channel.id,
        message_id=ctx.message.id,
        content=message
    )

    pending_responses[ctx.message.id] = (ctx.channel, ctx.author)
    await ctx.send("Message sent to Claude Code. Waiting for response...")


@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Process commands
    await bot.process_commands(message)

    # Don't process commands twice
    if message.content.startswith("!"):
        return

    # In DMs, automatically bridge
    if isinstance(message.channel, discord.DMChannel):
        write_incoming(
            user=message.author.display_name,
            user_id=message.author.id,
            channel_id=message.channel.id,
            message_id=message.id,
            content=message.content
        )
        pending_responses[message.id] = (message.channel, message.author)
        await message.add_reaction("📨")  # Show message was received


# Run the bot
if __name__ == "__main__":
    print("Starting Claude Bridge Bot...")
    print(f"Watching: {OUTGOING_FILE}")
    print("Press Ctrl+C to stop")
    print()
    bot.run(DISCORD_BOT_TOKEN)
