from typing import Any

import anthropic

# Tool definitions for the agent (add/remove as needed)
TOOLS: list[anthropic.types.ToolParam] = []


def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Dispatch a tool call to its handler and return a string result."""
    raise NotImplementedError(f"Tool '{tool_name}' is not implemented.")
