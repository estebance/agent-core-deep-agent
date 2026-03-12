from unittest.mock import MagicMock, patch

import pytest

from agent_core_deep_agent.agent import DeepAgent
from agent_core_deep_agent.config import AgentConfig


@pytest.fixture
def config() -> AgentConfig:
    return AgentConfig(api_key="test-key")


def _make_end_turn_response(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def test_agent_run_returns_text(config: AgentConfig) -> None:
    agent = DeepAgent(config=config)
    mock_response = _make_end_turn_response("Hello, world!")

    with patch.object(agent.client.messages, "create", return_value=mock_response):
        result = agent.run("Say hello.")

    assert result == "Hello, world!"
