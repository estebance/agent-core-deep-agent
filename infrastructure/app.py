#!/usr/bin/env python3
import os

import aws_cdk as cdk
from stacks.agent_stack import AgentStack

APP_ENV = os.getenv("APP_ENV", "dev")
BASE_STACK_NAME = "agent-core-deep-agent"

FULL_STACK_NAME = f"{BASE_STACK_NAME}-{APP_ENV}"


app = cdk.App()

AgentStack(
    app,
    FULL_STACK_NAME,
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1",
    ),
)
app.synth()
