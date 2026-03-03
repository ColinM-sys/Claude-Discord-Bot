#!/usr/bin/env python3
"""
Claude Power Bot - Full Featured Discord Bot
- Claude AI responses
- File reading from your project
- Code execution
- Web search
- Bridge to Claude Code
- Conversation memory
"""

import discord
from discord.ext import commands, tasks
import httpx
import asyncio
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Project root for file access
PROJECT_ROOT = Path(__file__).parent

# Bridge files
BRIDGE_DIR = PROJECT_ROOT / "bridge"
INCOMING_FILE = BRIDGE_DIR / "incoming.txt"
OUTGOING_FILE = BRIDGE_DIR / "outgoing.txt"
BRIDGE_DIR.mkdir(exist_ok=True)

# Conversation memory (per user)
conversations = {}  # user_id -> list of messages

# Allowed users file (users who can receive DMs from the bot)
ALLOWED_USERS_FILE = BRIDGE_DIR / "allowed_users.txt"
PENDING_REQUESTS_FILE = BRIDGE_DIR / "pending_requests.json"

# Bot owner ID - set this to your Discord user ID
BOT_OWNER_ID = None  # Will be set from first bridge message with user_id

def load_allowed_users():
    """Load allowed user IDs from file."""
    if not ALLOWED_USERS_FILE.exists():
        return set()
    with open(ALLOWED_USERS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_allowed_user(user_id: int):
    """Add a user to the allowed list."""
    with open(ALLOWED_USERS_FILE, "a") as f:
        f.write(f"{user_id}\n")

def remove_allowed_user(user_id: int):
    """Remove a user from the allowed list."""
    allowed = load_allowed_users()
    allowed.discard(str(user_id))
    with open(ALLOWED_USERS_FILE, "w") as f:
        f.write("\n".join(allowed) + "\n" if allowed else "")

def is_user_allowed(user_id: int) -> bool:
    """Check if a user is allowed to receive DMs."""
    return str(user_id) in load_allowed_users()

def load_pending_requests():
    """Load pending access requests."""
    if not PENDING_REQUESTS_FILE.exists():
        return {}
    with open(PENDING_REQUESTS_FILE, "r") as f:
        return json.load(f)

def save_pending_requests(requests: dict):
    """Save pending requests."""
    with open(PENDING_REQUESTS_FILE, "w") as f:
        json.dump(requests, f)

def add_pending_request(user_id: int, username: str):
    """Add a user to pending requests."""
    requests = load_pending_requests()
    requests[str(user_id)] = {"username": username, "timestamp": datetime.now().isoformat()}
    save_pending_requests(requests)

def remove_pending_request(user_id: int):
    """Remove a user from pending requests."""
    requests = load_pending_requests()
    requests.pop(str(user_id), None)
    save_pending_requests(requests)

def is_request_pending(user_id: int) -> bool:
    """Check if user has a pending request."""
    return str(user_id) in load_pending_requests()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# ============= CLAUDE AI =============
async def ask_claude(question: str, system_prompt: str = None, user_id: int = None) -> str:
    """Ask Claude with optional conversation memory."""
    messages = []

    # Add conversation history if available
    if user_id and user_id in conversations:
        messages.extend(conversations[user_id][-10:])  # Last 10 messages

    messages.append({"role": "user", "content": question})

    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 2000,
        "messages": messages
    }

    if system_prompt:
        payload["system"] = system_prompt

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                json=payload,
                timeout=60.0
            )

            if response.status_code == 200:
                data = response.json()
                answer = data["content"][0]["text"]

                # Save to conversation memory
                if user_id:
                    if user_id not in conversations:
                        conversations[user_id] = []
                    conversations[user_id].append({"role": "user", "content": question})
                    conversations[user_id].append({"role": "assistant", "content": answer})
                    # Keep only last 20 messages
                    conversations[user_id] = conversations[user_id][-20:]

                return answer
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"


# ============= FILE OPERATIONS =============
def read_file(filepath: str) -> str:
    """Read a file from the project."""
    try:
        # Security: only allow files within project
        full_path = (PROJECT_ROOT / filepath).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT.resolve())):
            return "Error: Access denied - outside project directory"

        if not full_path.exists():
            return f"Error: File not found: {filepath}"

        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if len(content) > 3000:
            return content[:3000] + f"\n... (truncated, {len(content)} total chars)"
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def list_files(directory: str = ".") -> str:
    """List files in a directory."""
    try:
        full_path = (PROJECT_ROOT / directory).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT.resolve())):
            return "Error: Access denied"

        files = []
        for item in full_path.iterdir():
            prefix = "[DIR] " if item.is_dir() else "      "
            files.append(f"{prefix}{item.name}")

        return "\n".join(sorted(files)[:50]) or "Empty directory"
    except Exception as e:
        return f"Error: {str(e)}"


# ============= CODE EXECUTION =============
def run_python(code: str) -> str:
    """Execute Python code safely."""
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(PROJECT_ROOT)
        )
        output = result.stdout + result.stderr
        return output[:1500] if output else "Code executed (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (10s limit)"
    except Exception as e:
        return f"Error: {str(e)}"


def run_command(cmd: str) -> str:
    """Run a shell command (limited)."""
    allowed = ["dir", "ls", "echo", "date", "whoami", "git status", "git log", "pip list"]

    if not any(cmd.startswith(a) for a in allowed):
        return f"Error: Command not allowed. Allowed: {', '.join(allowed)}"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(PROJECT_ROOT)
        )
        output = result.stdout + result.stderr
        return output[:1500] if output else "Command executed (no output)"
    except Exception as e:
        return f"Error: {str(e)}"


# ============= BRIDGE =============
def write_to_bridge(user: str, user_id: int, channel_id: int, content: str):
    """Write message to bridge for Claude Code."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "user_id": user_id,
        "channel_id": channel_id,
        "content": content
    }
    with open(INCOMING_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


def read_bridge_responses():
    """Read responses from Claude Code."""
    if not OUTGOING_FILE.exists():
        return []

    with open(OUTGOING_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    # Clear file
    with open(OUTGOING_FILE, "w") as f:
        f.write("")

    responses = []
    for line in content.split("\n"):
        if line.strip():
            try:
                responses.append(json.loads(line))
            except:
                responses.append({"content": line})
    return responses


# ============= BOT EVENTS =============
@bot.event
async def on_ready():
    print("=" * 50)
    print("  Claude Power Bot is online!")
    print("=" * 50)
    print(f"  Bot: {bot.user.name}")
    print(f"  Project: {PROJECT_ROOT}")
    print("=" * 50)
    print("  Commands:")
    print("    !ask <question>   - Ask Claude")
    print("    !read <file>      - Read a file")
    print("    !ls [dir]         - List files")
    print("    !py <code>        - Run Python")
    print("    !cmd <command>    - Run command")
    print("    !bridge <msg>     - Send to Claude Code")
    print("    !clear            - Clear memory")
    print("    !help             - Show help")
    print("=" * 50)
    check_bridge.start()


@tasks.loop(seconds=1)
async def check_bridge():
    """Check for Claude Code responses."""
    for resp in read_bridge_responses():
        channel_id = resp.get("channel_id")
        content = resp.get("content", "")
        if channel_id and content:
            try:
                # Try to get channel (works for guild channels)
                channel = bot.get_channel(channel_id)
                if not channel:
                    # For DM channels, need to fetch
                    channel = await bot.fetch_channel(channel_id)
                if channel:
                    # Split long messages
                    for i in range(0, len(content), 1900):
                        await channel.send(content[i:i+1900])
                    print(f"[BRIDGE] Sent response to channel {channel_id}")
            except Exception as e:
                print(f"[BRIDGE ERROR] Could not send to {channel_id}: {e}")


# ============= COMMANDS =============
@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="Claude Power Bot", color=discord.Color.blue())
    embed.add_field(name="!ask <question>", value="Ask Claude AI anything", inline=False)
    embed.add_field(name="!read <file>", value="Read a file from the project", inline=False)
    embed.add_field(name="!ls [directory]", value="List files in directory", inline=False)
    embed.add_field(name="!py <code>", value="Execute Python code", inline=False)
    embed.add_field(name="!cmd <command>", value="Run shell command (limited)", inline=False)
    embed.add_field(name="!bridge <message>", value="Send to Claude Code session", inline=False)
    embed.add_field(name="!clear", value="Clear conversation memory", inline=False)
    embed.add_field(name="--- Access Control ---", value="Owner commands for managing who can DM the bot", inline=False)
    embed.add_field(name="!setowner", value="Set yourself as bot owner (first use only)", inline=False)
    embed.add_field(name="!pending", value="View pending access requests", inline=False)
    embed.add_field(name="!approve <id>", value="Approve a user's access request", inline=False)
    embed.add_field(name="!deny <id>", value="Deny a user's access request", inline=False)
    embed.add_field(name="!revoke <id>", value="Revoke a user's access", inline=False)
    embed.set_footer(text="Powered by Claude AI")
    await ctx.send(embed=embed)


@bot.command(name="ask")
async def ask_cmd(ctx, *, question: str = None):
    if not question:
        await ctx.send("Usage: `!ask <question>`")
        return

    async with ctx.typing():
        answer = await ask_claude(
            question,
            system_prompt="You are a helpful AI assistant. Be concise but thorough.",
            user_id=ctx.author.id
        )

    # Send response
    if len(answer) > 1900:
        for i in range(0, len(answer), 1900):
            await ctx.send(answer[i:i+1900])
    else:
        await ctx.send(answer)


@bot.command(name="read")
async def read_cmd(ctx, *, filepath: str = None):
    if not filepath:
        await ctx.send("Usage: `!read <filepath>`\nExample: `!read README.md`")
        return

    content = read_file(filepath)

    embed = discord.Embed(title=f"File: {filepath}", color=discord.Color.green())
    embed.description = f"```\n{content[:4000]}\n```"
    await ctx.send(embed=embed)


@bot.command(name="ls")
async def ls_cmd(ctx, directory: str = "."):
    files = list_files(directory)
    embed = discord.Embed(title=f"Files in: {directory}", color=discord.Color.blue())
    embed.description = f"```\n{files}\n```"
    await ctx.send(embed=embed)


@bot.command(name="py")
async def py_cmd(ctx, *, code: str = None):
    if not code:
        await ctx.send("Usage: `!py <python code>`\nExample: `!py print(2+2)`")
        return

    output = run_python(code)
    embed = discord.Embed(title="Python Output", color=discord.Color.orange())
    embed.description = f"```\n{output}\n```"
    await ctx.send(embed=embed)


@bot.command(name="cmd")
async def cmd_cmd(ctx, *, command: str = None):
    if not command:
        await ctx.send("Usage: `!cmd <command>`\nAllowed: dir, ls, echo, date, git status, git log")
        return

    output = run_command(command)
    embed = discord.Embed(title=f"Command: {command}", color=discord.Color.purple())
    embed.description = f"```\n{output}\n```"
    await ctx.send(embed=embed)


@bot.command(name="bridge")
async def bridge_cmd(ctx, *, message: str = None):
    if not message:
        await ctx.send("Usage: `!bridge <message for Claude Code>`")
        return

    write_to_bridge(ctx.author.display_name, ctx.author.id, ctx.channel.id, message)
    await ctx.send("Sent to Claude Code! Response will appear here when ready.")


@bot.command(name="clear")
async def clear_cmd(ctx):
    if ctx.author.id in conversations:
        del conversations[ctx.author.id]
    await ctx.send("Conversation memory cleared!")


@bot.command(name="allow")
async def allow_cmd(ctx):
    """Allow the bot to DM you."""
    if not is_user_allowed(ctx.author.id):
        save_allowed_user(ctx.author.id)
        await ctx.send(f"You've been added to the allowed list! The bot can now DM you.")
    else:
        await ctx.send("You're already on the allowed list!")


@bot.command(name="request")
async def request_cmd(ctx):
    """Request access to DM the bot."""
    if is_user_allowed(ctx.author.id):
        await ctx.send("You already have access!")
        return

    if is_request_pending(ctx.author.id):
        await ctx.send("Your request is already pending approval.")
        return

    add_pending_request(ctx.author.id, ctx.author.display_name)
    await ctx.send("Access request submitted! The bot owner will review it.")

    # Notify via bridge
    write_to_bridge("SYSTEM", 0, ctx.channel.id,
                    f"ACCESS REQUEST: {ctx.author.display_name} (ID: {ctx.author.id}) wants to use the bot.")


@bot.command(name="pending")
async def pending_cmd(ctx):
    """View pending access requests (owner only)."""
    global BOT_OWNER_ID
    if BOT_OWNER_ID and ctx.author.id != BOT_OWNER_ID:
        await ctx.send("Only the bot owner can view pending requests.")
        return

    requests = load_pending_requests()
    if not requests:
        await ctx.send("No pending requests.")
        return

    msg = "**Pending Access Requests:**\n"
    for user_id, info in requests.items():
        msg += f"- {info['username']} (ID: {user_id})\n"
    msg += "\nUse `!approve <user_id>` or `!deny <user_id>` to respond."
    await ctx.send(msg)


@bot.command(name="approve")
async def approve_cmd(ctx, user_id: int = None):
    """Approve a user's access request (owner only)."""
    global BOT_OWNER_ID
    if BOT_OWNER_ID and ctx.author.id != BOT_OWNER_ID:
        await ctx.send("Only the bot owner can approve requests.")
        return

    if not user_id:
        await ctx.send("Usage: `!approve <user_id>`")
        return

    if not is_request_pending(user_id):
        await ctx.send("No pending request from that user.")
        return

    requests = load_pending_requests()
    username = requests.get(str(user_id), {}).get("username", "Unknown")

    save_allowed_user(user_id)
    remove_pending_request(user_id)
    await ctx.send(f"Approved! {username} can now DM the bot.")

    # Try to notify the user
    try:
        user = await bot.fetch_user(user_id)
        await user.send("Your access request has been approved! You can now DM me.")
    except:
        pass


@bot.command(name="deny")
async def deny_cmd(ctx, user_id: int = None):
    """Deny a user's access request (owner only)."""
    global BOT_OWNER_ID
    if BOT_OWNER_ID and ctx.author.id != BOT_OWNER_ID:
        await ctx.send("Only the bot owner can deny requests.")
        return

    if not user_id:
        await ctx.send("Usage: `!deny <user_id>`")
        return

    if not is_request_pending(user_id):
        await ctx.send("No pending request from that user.")
        return

    requests = load_pending_requests()
    username = requests.get(str(user_id), {}).get("username", "Unknown")

    remove_pending_request(user_id)
    await ctx.send(f"Denied request from {username}.")


@bot.command(name="revoke")
async def revoke_cmd(ctx, user_id: int = None):
    """Revoke a user's access (owner only)."""
    global BOT_OWNER_ID
    if BOT_OWNER_ID and ctx.author.id != BOT_OWNER_ID:
        await ctx.send("Only the bot owner can revoke access.")
        return

    if not user_id:
        await ctx.send("Usage: `!revoke <user_id>`")
        return

    if not is_user_allowed(user_id):
        await ctx.send("That user doesn't have access.")
        return

    remove_allowed_user(user_id)
    await ctx.send(f"Revoked access for user {user_id}.")


@bot.command(name="setowner")
async def setowner_cmd(ctx):
    """Set yourself as the bot owner (first use only)."""
    global BOT_OWNER_ID
    if BOT_OWNER_ID:
        await ctx.send("Owner is already set.")
        return

    BOT_OWNER_ID = ctx.author.id
    save_allowed_user(ctx.author.id)  # Owner is automatically allowed
    await ctx.send(f"You are now the bot owner! Your ID: {ctx.author.id}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    if message.content.startswith("!"):
        return

    # ALL DMs go directly to Claude Code via bridge
    if isinstance(message.channel, discord.DMChannel):
        # Check if user is allowed
        if not is_user_allowed(message.author.id):
            if is_request_pending(message.author.id):
                await message.channel.send("Your access request is pending approval. Please wait.")
            else:
                # Auto-submit a request for them
                add_pending_request(message.author.id, message.author.display_name)
                await message.channel.send(
                    "You need access to use this bot.\n"
                    "I've submitted an access request for you. The owner will review it."
                )
                # Notify via bridge
                write_to_bridge("SYSTEM", 0, 0,
                    f"ACCESS REQUEST: {message.author.display_name} (ID: {message.author.id}) wants to DM the bot.")
            return

        write_to_bridge(message.author.display_name, message.author.id, message.channel.id, message.content)
        await message.add_reaction("📨")  # Show message was sent to Claude Code
        return


if __name__ == "__main__":
    print("Starting Claude Power Bot...")
    bot.run(DISCORD_BOT_TOKEN)
