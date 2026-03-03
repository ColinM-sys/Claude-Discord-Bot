# Discord Webhook Tool for Claude Agent
#
# Usage in YAML:
#   functions:
#     discord:
#       _type: discord_webhook
#       webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
#       bot_name: "Claude Agent"

import httpx
from pydantic import Field

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig


class DiscordWebhookConfig(FunctionBaseConfig, name="discord_webhook"):
    """Tool for sending messages to Discord via webhooks."""

    webhook_url: str = Field(
        description="Discord webhook URL (get from Server Settings > Integrations > Webhooks)"
    )
    bot_name: str = Field(
        default="Claude Agent",
        description="Name displayed for the bot in Discord"
    )


@register_function(config_type=DiscordWebhookConfig)
async def discord_webhook_tool(config: DiscordWebhookConfig, _builder: Builder):
    """Send messages to Discord."""

    async def send_to_discord(message: str) -> str:
        """
        Send a message to Discord.

        Args:
            message: The message text to send to Discord

        Returns:
            Success or error message
        """
        payload = {
            "username": config.bot_name,
            "content": message,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    config.webhook_url,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code in [200, 204]:
                    return "Message sent to Discord successfully!"
                else:
                    return f"Discord error: {response.status_code} - {response.text}"

            except Exception as e:
                return f"Failed to send to Discord: {str(e)}"

    yield FunctionInfo.from_fn(
        send_to_discord,
        description="Send a message to Discord. Use this to post messages, alerts, or results to a Discord channel."
    )
