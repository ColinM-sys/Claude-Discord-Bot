# Claude Discord Bot

AI-powered Discord bots with Claude integration, file bridging, conversation memory, and user approval system. Includes three bot variants and a bridge system for connecting Discord to Claude Code.

## Bots

### NeMo Discord Bot (`nemo_discord_bot.py`)
The main bot — ask Claude questions directly from Discord with a user approval system.

**Commands:**
| Command | Description |
|---------|-------------|
| `!ask <question>` | Ask Claude AI a question |
| `!private` | Create a private thread for conversation |
| `!request` | Request access to use the bot |
| `!help` | Show available commands |
| `!approve @user` | (Owner) Approve a user |
| `!unapprove @user` | (Owner) Remove user approval |
| `!pending` | (Owner) View pending access requests |

### NeMo Power Bot (`nemo_power_bot.py`)
Full-featured bot with Claude AI, file access, code execution, web search, conversation memory, and Claude Code bridging.

**Additional capabilities:**
- Conversation memory (remembers last 20 messages per user)
- Read files from your project directory
- List project files
- Execute code snippets
- Bridge messages to/from Claude Code
- User allowlist and access request system

### NeMo Bridge Bot (`nemo_bridge_bot.py`)
Lightweight bot that bridges Discord messages to Claude Code via local files.

**How it works:**
```
Discord User  →  bridge/incoming.txt  →  Claude Code / Bridge Watcher
                                              ↓
Discord User  ←  bridge/outgoing.txt  ←  Claude Code / Bridge Watcher
```

Messages are written to `bridge/incoming.txt` as JSON lines. Responses are read from `bridge/outgoing.txt` and sent back to Discord. This lets Claude Code respond to Discord messages without a direct API connection.

### Bridge Watcher (`bridge_watcher.py`)
Background process that monitors `bridge/incoming.txt` and auto-responds using the Claude API. Pairs with the Bridge Bot for autonomous Discord responses.

## Workflows

Pre-configured YAML workflows for NeMo Agent Toolkit:

| File | Description |
|------|-------------|
| `discord_agent_workflow.yaml` | Discord-integrated agent workflow |
| `action_agent_workflow.yaml` | Action-based agent workflow |
| `claude_workflow.yaml` | Claude-specific workflow config |
| `my_workflow.yaml` | Custom workflow template |

## Custom Plugins

| Plugin | Description |
|--------|-------------|
| `my_plugins/anthropic_provider/` | Anthropic API provider for NeMo |
| `my_plugins/nat_anthropic/` | NeMo Agent Toolkit Anthropic LLM integration |
| `my_plugins/custom_tools/` | Custom tools: command execution, Discord integration, submit tool |

## Installation

### Prerequisites

- Python 3.8+
- A [Discord Bot Token](https://discord.com/developers/applications)
- An [Anthropic API Key](https://console.anthropic.com/)

### Setup

```bash
# Clone the repo
git clone https://github.com/ColinM-sys/Claude-Discord-Bot.git
cd Claude-Discord-Bot

# Install dependencies
pip install discord.py httpx anthropic

# Set environment variables
export DISCORD_BOT_TOKEN="your-discord-bot-token"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Creating a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. Go to **Bot** tab → click **Add Bot**
4. Enable these Privileged Gateway Intents:
   - **Message Content Intent**
   - **Server Members Intent** (optional)
5. Copy the bot token and set it as `DISCORD_BOT_TOKEN`
6. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Read Messages`, `Create Public Threads`, `Send Messages in Threads`, `Read Message History`
7. Open the generated URL to invite the bot to your server

### Running

```bash
# Main bot (recommended starting point)
python nemo_discord_bot.py

# Full-featured bot with file access, code exec, and memory
python nemo_power_bot.py

# Bridge bot (pair with bridge_watcher.py)
python nemo_bridge_bot.py

# Auto-responder for bridge (run alongside bridge bot)
python bridge_watcher.py
```

## User Approval System

The bot restricts access by default. Only approved users can use commands:

1. A new user types `!request` to request access
2. The bot owner sees pending requests with `!pending`
3. The owner approves with `!approve @user`
4. Approved users are saved to `approved_users.json` (persists across restarts)

The bot owner is automatically detected from the Discord application info.

## Project Structure

```
Claude-Discord-Bot/
├── nemo_discord_bot.py          # Main Claude AI bot
├── nemo_power_bot.py            # Full-featured bot (AI + files + code + memory)
├── nemo_bridge_bot.py           # File-based bridge bot
├── bridge_watcher.py            # Auto-responder for bridge
├── discord_bot.py               # Simple bot template
├── discord_chat.py              # Chat utility
├── bridge/
│   ├── incoming.txt             # Messages from Discord
│   ├── outgoing.txt             # Responses to Discord
│   ├── allowed_users.txt        # User allowlist
│   ├── pending_requests.json    # Pending access requests
│   └── seen.txt                 # Processed message tracking
├── my_plugins/
│   ├── anthropic_provider/      # Anthropic API provider
│   ├── nat_anthropic/           # NeMo Anthropic LLM integration
│   └── custom_tools/            # Custom Discord/command tools
├── action_agent_workflow.yaml   # Agent workflow config
├── claude_workflow.yaml         # Claude workflow config
├── discord_agent_workflow.yaml  # Discord agent workflow config
└── my_workflow.yaml             # Custom workflow template
```

## License

ISC
