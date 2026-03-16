from aws_cdk import Stack
from constructs import Construct

from .agent_core.agent_core import DeepAgentCore
from .cognito.cognito import DeepAgentCognito


class AgentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        DeepAgentCognito(self, f"DeepAgentCognito")

        DeepAgentCore(self, f"DeepAgentCore")
