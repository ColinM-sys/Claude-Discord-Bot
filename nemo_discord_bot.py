#!/usr/bin/env python3
"""
NeMo Agent Discord Bot
A full Discord bot powered by Claude AI

Commands:
    !ask <question>     - Ask Claude a question
    !private            - Create a private thread for conversation
    !help               - Show help
    !approve <@user>    - (Owner only) Approve a user
    !unapprove <@user>  - (Owner only) Remove user approval
    !pending            - (Owner only) See pending approval requests
    !request            - Request access to use the bot

Run: python nemo_discord_bot.py
"""

import discord
from discord.ext import commands
import httpx
import asyncio
import json
import os

# Configuration
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Your Discord user ID (for owner-only commands) - we'll get this automatically
OWNER_ID = None

# Approved users file
APPROVED_USERS_FILE = "approved_users.json"
PENDING_REQUESTS_FILE = "pending_requests.json"

def load_approved_users():
    """Load approved users from file."""
    if os.path.exists(APPROVED_USERS_FILE):
        with open(APPROVED_USERS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_approved_users(users):
    """Save approved users to file."""
    with open(APPROVED_USERS_FILE, 'w') as f:
        json.dump(list(users), f)

def load_pending_requests():
    """Load pending requests from file."""
    if os.path.exists(PENDING_REQUESTS_FILE):
        with open(PENDING_REQUESTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_pending_requests(requests):
    """Save pending requests to file."""
    with open(PENDING_REQUESTS_FILE, 'w') as f:
        json.dump(requests, f)

# Load approved users on startup
approved_users = load_approved_users()
pending_requests = load_pending_requests()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


async def ask_claude(question: str, system_prompt: str = None) -> str:
    """Ask Claude a question and get a response."""
    messages = [{"role": "user", "content": question}]

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
                return data["content"][0]["text"]
            else:
                return f"Error: {response.status_code} - {response.text[:200]}"
        except Exception as e:
            return f"Error connecting to Claude: {str(e)}"


def is_approved(user_id):
    """Check if a user is approved to use the bot."""
    return user_id in approved_users or user_id == OWNER_ID

async def check_approval(ctx):
    """Check if user is approved, send denial message if not."""
    if is_approved(ctx.author.id):
        return True

    embed = discord.Embed(
        title="Access Denied",
        description="You need approval to use this bot.\n\nUse `!request` to request access from the owner.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
    return False

@bot.event
async def on_ready():
    global OWNER_ID
    print(f"=" * 50)
    print(f"  NeMo Agent Bot is online!")
    print(f"=" * 50)
    print(f"  Logged in as: {bot.user.name}")
    print(f"  Bot ID: {bot.user.id}")
    print(f"  Servers: {len(bot.guilds)}")
    print(f"=" * 50)
    print(f"  Commands:")
    print(f"    !ask <question>  - Ask Claude")
    print(f"    !private         - Create private thread")
    print(f"    !help            - Show help")
    print(f"    !approve @user   - Approve user (owner)")
    print(f"    !unapprove @user - Remove approval (owner)")
    print(f"    !pending         - See pending requests (owner)")
    print(f"    !request         - Request access")
    print(f"=" * 50)

    # Get owner ID from first guild
    if bot.guilds:
        app_info = await bot.application_info()
        OWNER_ID = app_info.owner.id
        print(f"  Owner ID: {OWNER_ID}")
        print(f"  Approved users: {len(approved_users)}")


@bot.command(name="request")
async def request_command(ctx):
    """Request access to use the bot."""
    global pending_requests

    if is_approved(ctx.author.id):
        await ctx.send("You're already approved to use this bot!")
        return

    user_id = str(ctx.author.id)
    if user_id in pending_requests:
        await ctx.send("You already have a pending request. Please wait for the owner to approve it.")
        return

    pending_requests[user_id] = {
        "username": str(ctx.author),
        "display_name": ctx.author.display_name,
        "requested_at": str(discord.utils.utcnow())
    }
    save_pending_requests(pending_requests)

    embed = discord.Embed(
        title="Access Requested",
        description="Your request has been sent to the bot owner.\nYou'll be notified when approved.",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

    # Notify owner
    if OWNER_ID:
        owner = await bot.fetch_user(OWNER_ID)
        if owner:
            notify_embed = discord.Embed(
                title="New Access Request",
                description=f"**{ctx.author}** ({ctx.author.display_name}) wants access.\n\nUse `!approve @{ctx.author}` to approve.",
                color=discord.Color.orange()
            )
            try:
                await owner.send(embed=notify_embed)
            except:
                pass


@bot.command(name="approve")
async def approve_command(ctx, member: discord.Member = None):
    """Approve a user to use the bot (owner only)."""
    global approved_users, pending_requests

    if ctx.author.id != OWNER_ID:
        await ctx.send("Only the bot owner can approve users.")
        return

    if not member:
        await ctx.send("Please mention a user to approve. Usage: `!approve @user`")
        return

    approved_users.add(member.id)
    save_approved_users(approved_users)

    # Remove from pending if present
    if str(member.id) in pending_requests:
        del pending_requests[str(member.id)]
        save_pending_requests(pending_requests)

    embed = discord.Embed(
        title="User Approved",
        description=f"**{member}** can now use the bot!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    # Notify the user
    try:
        notify_embed = discord.Embed(
            title="Access Granted!",
            description="You've been approved to use NeMo Agent Bot!\n\nTry `!help` to see available commands.",
            color=discord.Color.green()
        )
        await member.send(embed=notify_embed)
    except:
        pass


@bot.command(name="unapprove")
async def unapprove_command(ctx, member: discord.Member = None):
    """Remove a user's approval (owner only)."""
    global approved_users

    if ctx.author.id != OWNER_ID:
        await ctx.send("Only the bot owner can unapprove users.")
        return

    if not member:
        await ctx.send("Please mention a user to unapprove. Usage: `!unapprove @user`")
        return

    if member.id in approved_users:
        approved_users.discard(member.id)
        save_approved_users(approved_users)
        await ctx.send(f"**{member}** has been removed from approved users.")
    else:
        await ctx.send(f"**{member}** wasn't in the approved list.")


@bot.command(name="pending")
async def pending_command(ctx):
    """Show pending access requests (owner only)."""
    if ctx.author.id != OWNER_ID:
        await ctx.send("Only the bot owner can view pending requests.")
        return

    if not pending_requests:
        await ctx.send("No pending access requests.")
        return

    embed = discord.Embed(
        title="Pending Access Requests",
        color=discord.Color.orange()
    )

    for user_id, info in pending_requests.items():
        embed.add_field(
            name=info["display_name"],
            value=f"Username: {info['username']}\nID: {user_id}",
            inline=False
        )

    embed.set_footer(text="Use !approve @user to approve")
    await ctx.send(embed=embed)


@bot.command(name="approved")
async def approved_command(ctx):
    """Show approved users (owner only)."""
    if ctx.author.id != OWNER_ID:
        await ctx.send("Only the bot owner can view approved users.")
        return

    if not approved_users:
        await ctx.send("No approved users yet.")
        return

    embed = discord.Embed(
        title="Approved Users",
        description=f"Total: {len(approved_users)} users",
        color=discord.Color.green()
    )

    user_list = []
    for user_id in approved_users:
        try:
            user = await bot.fetch_user(user_id)
            user_list.append(f"• {user} (ID: {user_id})")
        except:
            user_list.append(f"• Unknown (ID: {user_id})")

    embed.add_field(name="Users", value="\n".join(user_list) or "None", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="help")
async def help_command(ctx):
    """Show help message."""
    embed = discord.Embed(
        title="NeMo Agent Bot - Help",
        description="AI-powered assistant using Claude",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="!ask <question>",
        value="Ask Claude any question",
        inline=False
    )
    embed.add_field(
        name="!private",
        value="Create a private thread for conversation",
        inline=False
    )
    embed.add_field(
        name="!calc <expression>",
        value="Calculate math (e.g., !calc 42 * 17)",
        inline=False
    )
    embed.add_field(
        name="!request",
        value="Request access to use the bot",
        inline=False
    )

    # Show owner commands if owner
    if ctx.author.id == OWNER_ID:
        embed.add_field(
            name="Owner Commands",
            value="!approve @user - Approve a user\n!unapprove @user - Remove approval\n!pending - View pending requests\n!approved - View approved users",
            inline=False
        )

    embed.set_footer(text="Powered by Claude AI + NeMo Agent Toolkit")
    await ctx.send(embed=embed)


@bot.command(name="ask")
async def ask_command(ctx, *, question: str = None):
    """Ask Claude a question."""
    if not await check_approval(ctx):
        return

    if not question:
        await ctx.send("Please provide a question! Usage: `!ask <your question>`")
        return

    # Show typing indicator
    async with ctx.typing():
        answer = await ask_claude(question)

    # Split long responses
    if len(answer) > 1900:
        chunks = [answer[i:i+1900] for i in range(0, len(answer), 1900)]
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"Response ({i+1}/{len(chunks)})" if len(chunks) > 1 else "Response",
                description=chunk,
                color=discord.Color.green()
            )
            if i == 0:
                embed.set_author(name=f"Q: {question[:100]}...")
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            description=answer,
            color=discord.Color.green()
        )
        embed.set_author(name=f"Q: {question[:100]}")
        embed.set_footer(text=f"Asked by {ctx.author.display_name}")
        await ctx.send(embed=embed)


@bot.command(name="calc")
async def calc_command(ctx, *, expression: str = None):
    """Calculate a math expression."""
    if not await check_approval(ctx):
        return

    if not expression:
        await ctx.send("Please provide an expression! Usage: `!calc 42 * 17`")
        return

    async with ctx.typing():
        answer = await ask_claude(
            f"Calculate this and give ONLY the numerical answer, nothing else: {expression}"
        )

    await ctx.send(f"**{expression}** = **{answer.strip()}**")


@bot.command(name="private")
async def private_command(ctx):
    """Create a private thread for conversation."""
    if not await check_approval(ctx):
        return

    try:
        # Create a private thread
        thread = await ctx.channel.create_thread(
            name=f"Private - {ctx.author.display_name}",
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        # Send welcome message in thread
        embed = discord.Embed(
            title="Private Conversation",
            description="This is your private thread with NeMo Agent.\n\n"
                       "Just type your messages here - no need for commands!\n"
                       "I'll respond to everything you say.",
            color=discord.Color.purple()
        )
        await thread.send(embed=embed)
        await ctx.send(f"Created private thread: {thread.mention}", delete_after=10)

    except discord.Forbidden:
        await ctx.send("I don't have permission to create threads!")
    except Exception as e:
        await ctx.send(f"Error creating thread: {str(e)}")


@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Process commands first
    await bot.process_commands(message)

    # Don't respond to commands
    if message.content.startswith("!"):
        return

    # Auto-respond in DMs (direct messages)
    if isinstance(message.channel, discord.DMChannel):
        # Check approval for DMs
        if not is_approved(message.author.id):
            embed = discord.Embed(
                title="Access Denied",
                description="You need approval to DM this bot.\n\nGo to the server and use `!request` to request access.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return

        async with message.channel.typing():
            response = await ask_claude(
                message.content,
                system_prompt="You are a helpful AI assistant in a Discord DM. Keep responses concise but helpful."
            )

        # Split long responses
        if len(response) > 1900:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await message.channel.send(chunk)
        else:
            await message.channel.send(response)
        return

    # Auto-respond in private threads (no command needed)
    if isinstance(message.channel, discord.Thread):
        if message.channel.name.startswith("Private -"):
            # Check approval for threads
            if not is_approved(message.author.id):
                embed = discord.Embed(
                    title="Access Denied",
                    description="You need approval to use this bot.\n\nUse `!request` in the main channel to request access.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                return

            async with message.channel.typing():
                response = await ask_claude(
                    message.content,
                    system_prompt="You are a helpful AI assistant in a Discord chat. Keep responses concise but helpful."
                )

            # Split long responses
            if len(response) > 1900:
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(response)


# Run the bot
if __name__ == "__main__":
    print("Starting NeMo Agent Discord Bot...")
    print("Press Ctrl+C to stop")
    print()
    bot.run(DISCORD_BOT_TOKEN)
