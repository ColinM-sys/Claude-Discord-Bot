# Claude Agent Discord Bots

A system of Discord bots powered by Claude AI. These bots work together to create a complete AI-powered Discord experience — from simple Q&A to remote code execution and bridging into Claude Code sessions. They use the Anthropic API and discord.py.

## How They Work Together

The bots form a layered system where each component handles a different part of the pipeline:

```
Discord User
    │
    ├── !ask / !private / DMs ──► Claude Agent Bot ──► Claude API ──► Response in Discord
    │
    ├── !read / !py / !cmd ─────► Claude Power Bot ──► Local files, code execution
    │                                    │
    ├── !bridge / DMs ──────────► Bridge Bot ────────► bridge/incoming.txt
    │                                                       │
    │                                                  Claude Code (reads file)
    │                                                       │
    │                                                  bridge/outgoing.txt
    │                                                       │
    │                              Bot picks up response ◄──┘
    │                                    │
    │                              Response sent to Discord
    │
    ├── CLI one-shot ───────────► Webhook Bot ───────► Discord channel (via webhook)
    │
    └── Workflow automation ────► Custom Tool ────────► Discord channel (via webhook)
```

- **Agent Bot** handles user-facing interaction — questions, private threads, access control
- **Power Bot** adds project-level tools — file access, code execution, conversation memory
- **Bridge Bot / Power Bot bridge** connects Discord to a running Claude Code session through file-based IPC, letting you control your desktop from your phone
- **Webhook Bot + Interactive Chat** provide quick CLI-to-Discord posting for scripts and one-off questions
- **Custom Tool** plugs into NAT agent workflows so automated agents can post to Discord

You can run them individually or combine them. For the full experience, run the **Power Bot** alongside **Claude Code** — users chat in Discord, the bot handles simple questions via the API, and complex tasks get bridged to Claude Code for full IDE-level processing.

## Bots

### Claude Agent Bot (`claude_discord_bot.py`)
The main Discord bot. Runs as a persistent bot in your server.

**Features:**
- `!ask <question>` — Ask Claude anything
- `!private` — Create a private thread for 1-on-1 conversation (no commands needed inside threads)
- `!calc <expression>` — Quick math calculations
- `!request` — Request access to use the bot
- DM support — approved users can DM the bot directly

**Access Control:**
- User approval system — only approved users can interact
- `!approve @user` / `!unapprove @user` — Owner manages access
- `!pending` — View pending access requests
- `!approved` — View approved users list

**Run:** `python claude_discord_bot.py`

---

### Claude Power Bot (`claude_power_bot.py`)
Full-featured bot with file access, code execution, and a bridge to Claude Code.

**Features:**
- Everything the Agent Bot does, plus:
- `!read <file>` — Read files from the project directory
- `!ls [directory]` — List files
- `!py <code>` — Execute Python code (10s timeout)
- `!cmd <command>` — Run shell commands (limited to safe commands: dir, ls, echo, date, git status, git log, pip list)
- `!bridge <message>` — Send a message to a running Claude Code session
- `!clear` — Clear conversation memory
- Conversation memory — remembers context per user (last 20 messages)

**Bridge System:**
Messages sent via `!bridge` or DM are written to `bridge/incoming.txt`. Claude Code can read these and write responses to `bridge/outgoing.txt`, which the bot sends back to Discord.

**Run:** `python claude_power_bot.py`

---

### Bridge Bot (`claude_bridge_bot.py`)
Lightweight bot that only bridges Discord messages to Claude Code via files.

**Features:**
- `!bridge <message>` — Send a message to Claude Code
- DMs are automatically forwarded to Claude Code
- Responses from `bridge/outgoing.txt` are sent back to Discord

**Run:** `python claude_bridge_bot.py`

---

### Simple Webhook Bot (`discord_bot.py`)
One-shot script — ask Claude a question from the command line and post the answer to Discord via webhook.

**Run:** `python discord_bot.py "What is quantum computing?"`

No bot token needed — uses a Discord webhook URL instead.

---

### Interactive Chat (`discord_chat.py`)
CLI chat interface that also posts responses to Discord via webhook.

**Features:**
- Type questions interactively, Claude responds in terminal and Discord
- Type `local` to toggle Discord posting on/off
- Type `quit` to exit

**Run:** `python discord_chat.py`

---

### Custom Discord Tool (`my_plugins/custom_tools/discord_tool.py`)
A NAT workflow tool for sending messages to Discord from agent workflows.

**Usage in workflow YAML:**
```yaml
functions:
  discord:
    _type: discord_webhook
    webhook_url: "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
    bot_name: "Claude Agent"
```

## Setup

### Prerequisites
- Python 3.10+
- `pip install discord.py httpx`

### Environment Variables

| Variable | Used by | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Agent Bot, Power Bot, Bridge Bot | Bot token from [Discord Developer Portal](https://discord.com/developers/applications) |
| `ANTHROPIC_API_KEY` | All bots | API key from [Anthropic Console](https://console.anthropic.com/) |
| `DISCORD_WEBHOOK` | Webhook Bot, Interactive Chat | Webhook URL from Server Settings > Integrations > Webhooks |

Set them before running:
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

## Use Cases

**Full AI Pipeline (All Components)**
Run the Power Bot + Claude Code together for the complete experience. Users ask questions in Discord — simple ones get answered directly via the API, complex ones get bridged to Claude Code which can read files, edit code, run tests, and send results back through the bridge. The webhook bot and custom tool let automated scripts post updates to the same channels.

**Personal AI Assistant**
Run the Agent Bot in a private server. Use `!private` to create threads for different topics — the bot responds to everything in the thread without needing commands.

**Team Q&A**
Set up the Agent Bot in a team server. Use the approval system to control who can use it. Team members ask questions with `!ask` and everyone can see the answers.

**Remote Claude Code Control**
Run the Power Bot or Bridge Bot alongside Claude Code. Send commands from Discord on your phone, and Claude Code processes them on your desktop. Useful for monitoring long-running tasks or triggering actions remotely.

**Automated Notifications**
Use the webhook bot or custom tool in scripts/workflows to post results, alerts, or status updates to Discord channels. Chain this with the other bots so both humans and automated agents post to the same Discord channels.

**Quick Calculations**
Use `!calc` for fast math without leaving Discord — great for quick conversions, percentages, or estimates during conversations.
