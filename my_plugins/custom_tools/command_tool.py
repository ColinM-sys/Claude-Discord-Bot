# Custom tool to execute shell commands
#
# WARNING: This is powerful - use with caution!
# Usage in YAML:
#   functions:
#     run_command:
#       _type: shell_command
#       allowed_commands: ["git", "npm", "python"]

import asyncio
import subprocess
from pydantic import Field

from nat.tool.tool import ToolConfig, register_function


class ShellCommandConfig(ToolConfig, name="shell_command"):
    """Tool for executing shell commands."""

    allowed_commands: list[str] = Field(
        default_factory=lambda: ["echo", "date", "whoami"],
        description="List of allowed command prefixes for security"
    )
    working_dir: str = Field(
        default=".",
        description="Working directory for commands"
    )
    timeout: int = Field(
        default=30,
        description="Command timeout in seconds"
    )


@register_function(config_type=ShellCommandConfig)
async def shell_command_tool(config: ShellCommandConfig):
    """Execute shell commands."""

    async def run_command(command: str) -> str:
        """
        Execute a shell command.

        Args:
            command: The command to run

        Returns:
            Command output or error message
        """
        # Security check
        cmd_parts = command.split()
        if not cmd_parts:
            return "Error: Empty command"

        base_cmd = cmd_parts[0]
        if base_cmd not in config.allowed_commands:
            return f"Error: Command '{base_cmd}' not allowed. Allowed: {config.allowed_commands}"

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=config.working_dir
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=config.timeout
            )

            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""

            if error:
                return f"Output: {output}\nErrors: {error}"
            return output or "Command completed (no output)"

        except asyncio.TimeoutError:
            return f"Error: Command timed out after {config.timeout}s"
        except Exception as e:
            return f"Error: {str(e)}"

    yield run_command
