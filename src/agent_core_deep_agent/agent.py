from typing import Any

import anthropic

from agent_core_deep_agent.config import AgentConfig
from agent_core_deep_agent.tools import TOOLS, execute_tool


class DeepAgent:
    """Agentic loop powered by Claude with tool-use support."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()
        self.client = anthropic.Anthropic(api_key=self.config.api_key)

    def run(self, prompt: str) -> str:
        """Run the agent loop until a final text response is produced."""
        messages: list[anthropic.types.MessageParam] = [
            {"role": "user", "content": prompt}
        ]

        for _ in range(self.config.max_iterations):
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=self.config.system_prompt,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = self._handle_tool_calls(response.content)
                messages.append({"role": "user", "content": tool_results})
                continue

            break

        return self._extract_text(response)

    def _handle_tool_calls(
        self, content: list[anthropic.types.ContentBlock]
    ) -> list[anthropic.types.ToolResultBlockParam]:
        results: list[anthropic.types.ToolResultBlockParam] = []
        for block in content:
            if block.type != "tool_use":
                continue
            try:
                output = execute_tool(block.name, dict(block.input))  # type: ignore[arg-type]
            except Exception as exc:
                output = f"Error: {exc}"
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                }
            )
        return results

    def _extract_text(self, response: anthropic.types.Message) -> str:
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""
