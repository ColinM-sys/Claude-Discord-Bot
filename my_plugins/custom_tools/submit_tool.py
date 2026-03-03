# Custom tool to submit data to external systems
#
# This tool lets the agent send HTTP requests to any API/webhook
# Usage in YAML:
#   functions:
#     submit_data:
#       _type: http_submit
#       endpoint_url: "https://your-api.com/webhook"

import httpx
from pydantic import Field

from nat.tool.tool import ToolConfig, register_function


class HttpSubmitConfig(ToolConfig, name="http_submit"):
    """Tool for submitting data to external HTTP endpoints."""

    endpoint_url: str = Field(
        description="The URL to send data to"
    )
    method: str = Field(
        default="POST",
        description="HTTP method (POST, PUT, PATCH)"
    )
    headers: dict = Field(
        default_factory=dict,
        description="Additional headers to send"
    )


@register_function(config_type=HttpSubmitConfig)
async def http_submit_tool(config: HttpSubmitConfig):
    """Submit data to an external HTTP endpoint."""

    async def submit_data(data: str) -> str:
        """
        Send data to the configured endpoint.

        Args:
            data: The data/message to send (JSON string or text)

        Returns:
            Response from the server
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=config.method,
                    url=config.endpoint_url,
                    content=data,
                    headers={
                        "Content-Type": "application/json",
                        **config.headers
                    },
                    timeout=30.0
                )
                return f"Status: {response.status_code}, Response: {response.text[:500]}"
            except Exception as e:
                return f"Error submitting data: {str(e)}"

    yield submit_data
