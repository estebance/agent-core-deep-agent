import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    model: str = "claude-opus-4-6"
    max_tokens: int = 8096
    max_iterations: int = 10
    api_key: str = field(default_factory=lambda: os.environ["ANTHROPIC_API_KEY"])
    system_prompt: str = (
        "You are a deep research agent. You have access to tools to help you "
        "thoroughly investigate topics and produce well-reasoned, accurate responses."
    )
