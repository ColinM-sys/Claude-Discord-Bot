# Claude Discord Bot

A system of Discord bots powered by Claude AI. These bots work together to create a complete AI-powered Discord experience — from simple Q&A to remote code execution and bridging into Claude Code sessions. They use the Anthropic API and discord.py.

## How They Work Together

Each bot handles a different layer of the pipeline, and they combine to form a complete system:

```
Discord User
    │
    ├── !ask / !private / DMs ──► Agent Bot ──► Claude API ──► Response in Discord
    │
    ├── !read / !py / !cmd ─────► Power Bot ──► Local files, code execution
    │                                  │
    ├── !bridge / DMs ──────────► Bridge Bot ──► bridge/incoming.txt
    │                                                 │
    │                                            Claude Code (reads file)
    │                                                 │
    │                                            bridge/outgoing.txt
    │                                                 │
    │                            Bot picks up ◄───────┘
    │                            response → Discord
    │
    ├── CLI one-shot ───────────► Webhook Bot ──► Discord channel (via webhook)
    │
    └── CLI chat ──────────────► Interactive Chat ──► Discord channel (via webhook)
```

- **Agent Bot** handles user-facing interaction — questions, private threads, access control
- **Power Bot** adds project-level tools — file access, code execution, conversation memory
- **Bridge Bot / Power Bot bridge** connects Discord to a running Claude Code session through file-based IPC
- **Webhook Bot + Interactive Chat** provide quick CLI-to-Discord posting for scripts and one-off questions

For the full experience, run the **Power Bot** alongside **Claude Code** — users chat in Discord, simple questions get answered via the API, and complex tasks get bridged to Claude Code for full IDE-level processing.

## Bots

### Claude Agent Bot (`claude_discord_bot.py`)
The main Discord bot. Runs as a persistent bot in your server.

**Commands:**
| Command | Description |
|---------|-------------|
| `!ask <question>` | Ask Claude AI a question |
| `!private` | Create a private thread for conversation |
| `!calc <expression>` | Quick math calculations |
| `!request` | Request access to use the bot |
| `!help` | Show available commands |
| `!approve @user` | (Owner) Approve a user |
| `!unapprove @user` | (Owner) Remove user approval |
| `!pending` | (Owner) View pending access requests |

---

### Claude Power Bot (`claude_power_bot.py`)
Full-featured bot with Claude AI, file access, code execution, conversation memory, and Claude Code bridging.

**Additional commands:**
| Command | Description |
|---------|-------------|
| `!read <file>` | Read files from the project directory |
| `!ls [directory]` | List files |
| `!py <code>` | Execute Python code (10s timeout) |
| `!cmd <command>` | Run shell commands (limited to safe commands) |
| `!bridge <message>` | Send a message to Claude Code |
| `!clear` | Clear conversation memory |

**Bridge System:**
Messages sent via `!bridge` or DM are written to `bridge/incoming.txt`. Claude Code can read these and write responses to `bridge/outgoing.txt`, which the bot sends back to Discord.

---

### Claude Bridge Bot (`claude_bridge_bot.py`)
Lightweight bot that only bridges Discord messages to Claude Code via files.

```
Discord User  →  bridge/incoming.txt  →  Claude Code
                                              ↓
Discord User  ←  bridge/outgoing.txt  ←  Claude Code
```

---

### Bridge Watcher (`bridge_watcher.py`)
Background process that monitors `bridge/incoming.txt` and auto-responds using the Claude API. Pairs with the Bridge Bot for autonomous Discord responses.

---

### Simple Webhook Bot (`discord_bot.py`)
One-shot script — ask Claude a question from the command line and post the answer to Discord via webhook.

**Run:** `python discord_bot.py "What is quantum computing?"`

---

### Interactive Chat (`discord_chat.py`)
CLI chat interface that also posts responses to Discord via webhook.

**Run:** `python discord_chat.py`

## Setup

### Prerequisites
- Python 3.10+
- `pip install discord.py httpx anthropic`

### Environment Variables

| Variable | Used by | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Agent Bot, Power Bot, Bridge Bot | Bot token from [Discord Developer Portal](https://discord.com/developers/applications) |
| `ANTHROPIC_API_KEY` | All bots | API key from [Anthropic Console](https://console.anthropic.com/) |
| `DISCORD_WEBHOOK` | Webhook Bot, Interactive Chat | Webhook URL from Server Settings > Integrations > Webhooks |

```bash
export DISCORD_BOT_TOKEN="your-bot-token"
export ANTHROPIC_API_KEY="your-api-key"
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
```

### Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to Bot > create bot > copy token
4. Enable **Message Content Intent** under Privileged Gateway Intents
5. Go to OAuth2 > URL Generator > select `bot` scope > select permissions: Send Messages, Create Public Threads, Create Private Threads, Read Message History
6. Use the generated URL to invite the bot to your server

### Running

```bash
# Main bot (recommended starting point)
python claude_discord_bot.py

# Full-featured bot with file access, code exec, and memory
python claude_power_bot.py

# Bridge bot (pair with bridge_watcher.py)
python claude_bridge_bot.py

# Auto-responder for bridge
python bridge_watcher.py
```

## User Approval System

The bot restricts access by default. Only approved users can use commands:

1. A new user types `!request` to request access
2. The bot owner sees pending requests with `!pending`
3. The owner approves with `!approve @user`
4. Approved users are saved to `approved_users.json` (persists across restarts)

## Project Structure

```
Claude-Discord-Bot/
├── claude_discord_bot.py        # Main Claude AI bot
├── claude_power_bot.py          # Full-featured bot (AI + files + code + memory)
├── claude_bridge_bot.py         # File-based bridge bot
├── bridge_watcher.py            # Auto-responder for bridge
├── discord_bot.py               # Simple webhook bot
├── discord_chat.py              # Interactive CLI chat
├── DISCORD_BOTS.md              # Detailed documentation
└── bridge/
    ├── incoming.txt             # Messages from Discord
    ├── outgoing.txt             # Responses to Discord
    ├── allowed_users.txt        # User allowlist
    └── pending_requests.json    # Pending access requests
```

## Use Cases

- **Full AI Pipeline** — Power Bot + Claude Code for end-to-end: Discord chat → API answers + bridged code tasks → results back in Discord
- **Personal AI Assistant** — Agent Bot with `!private` threads for topic-based conversations
- **Team Q&A** — Agent Bot with approval system for controlled team access
- **Remote Claude Code Control** — Bridge Bot lets you control your desktop from Discord on your phone
- **Automated Notifications** — Webhook bot for scripts/workflows posting to Discord

