from __future__ import annotations

import os
from typing import TYPE_CHECKING

import aws_cdk as cdk
import aws_cdk.aws_ecr_assets as ecr_assets
from aws_cdk import (
    aws_bedrockagentcore as agentcore,
)
from aws_cdk import aws_iam as iam
from constructs import Construct

if TYPE_CHECKING:
    from infrastructure.stacks.cognito.cognito import DeepAgentCognito


class DeepAgentCore(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        cognito: DeepAgentCognito | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        region = cdk.Stack.of(self).region
        account_id = cdk.Stack.of(self).account

        # ecr_repo_id = f"{construct_id}-ecr"
        docker_asset_id = f"{construct_id}DockerAsset"
        agent_runtime_id = f"{construct_id}AgentRuntime"
        agent_runtime_endpoint_id = f"{construct_id}AgentRuntimeEndpoint"
        iam_role_id = f"{construct_id}AgtcoreRole"

        docker_asset = ecr_assets.DockerImageAsset(
            self, docker_asset_id, directory=os.path.join(os.getcwd())
        )

        # repository = ecr.Repository(self, ecr_repo_id, repository_name=ecr_repo_id)
        agentcore_runtime_version = kwargs.get("agentcore_runtime_version", "1")
        # The runtime by default create ECR permission only for the repository available in the account the stack is being deployed
        agent_runtime_artifact = agentcore.CfnRuntime.AgentRuntimeArtifactProperty(
            container_configuration=agentcore.CfnRuntime.ContainerConfigurationProperty(
                container_uri=docker_asset.image_uri
            )
        )
        # create the agent core memory

        # agent core runtime policy
        runtime_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="ECRImageAccess",
                    effect=iam.Effect.ALLOW,
                    actions=["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
                    resources=[f"arn:aws:ecr:{region}:{account_id}:repository/*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["logs:DescribeLogStreams", "logs:CreateLogGroup"],
                    resources=[
                        f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["logs:DescribeLogGroups"],
                    resources=[f"arn:aws:logs:{region}:{account_id}:log-group:*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                    resources=[
                        f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                    ],
                ),
                iam.PolicyStatement(
                    sid="ECRTokenAccess",
                    effect=iam.Effect.ALLOW,
                    actions=["ecr:GetAuthorizationToken"],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "xray:PutTraceSegments",
                        "xray:PutTelemetryRecords",
                        "xray:GetSamplingRules",
                        "xray:GetSamplingTargets",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["cloudwatch:PutMetricData"],
                    resources=["*"],
                    conditions={"StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}},
                ),
                iam.PolicyStatement(
                    sid="GetAgentAccessToken",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock-agentcore:GetWorkloadAccessToken",
                        "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                        "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
                    ],
                    resources=[
                        f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default",
                        f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default/workload-identity/agentName-*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="BedrockModelInvocation",
                    effect=iam.Effect.ALLOW,
                    actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                    resources=[
                        "arn:aws:bedrock:*::foundation-model/*",
                        f"arn:aws:bedrock:{region}:{account_id}:*",
                    ],
                ),
            ]
        )

        service_principal_role = iam.ServicePrincipal("bedrock-agentcore.amazonaws.com")
        runtime_role = iam.Role(
            self,
            iam_role_id,
            assumed_by=service_principal_role,
            description="IAM role for Bedrock AgentCore Runtime",
            inline_policies={"RuntimeAccessPolicy": runtime_policy},
        )

        # Build authorizer configuration only when a Cognito construct is provided
        authorizer_configuration = None
        if cognito is not None:
            # OIDC discovery URL for the Cognito User Pool
            discovery_url = cdk.Fn.join(
                "",
                [
                    "https://cognito-idp.",
                    region,
                    ".amazonaws.com/",
                    cognito.user_pool.user_pool_id,
                    "/.well-known/openid-configuration",
                ],
            )

            authorizer_configuration = agentcore.CfnRuntime.AuthorizerConfigurationProperty(
                custom_jwt_authorizer=agentcore.CfnRuntime.CustomJWTAuthorizerConfigurationProperty(
                    discovery_url=discovery_url,
                    allowed_audience=[
                        cognito.user_pool_client.user_pool_client_id,
                    ],
                    allowed_clients=[
                        cognito.user_pool_client.user_pool_client_id,
                    ],
                    allowed_scopes=["deepagent/invoke"],
                ),
            )

        agent_core_runtime = agentcore.CfnRuntime(
            self,
            agent_runtime_id,
            agent_runtime_artifact=agent_runtime_artifact,
            agent_runtime_name=agent_runtime_id,
            protocol_configuration="HTTP",
            network_configuration=agentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC"
            ),
            authorizer_configuration=authorizer_configuration,
            role_arn=runtime_role.role_arn,
            environment_variables={"AWS_REGION": region},
        )

        agentcore.CfnRuntimeEndpoint(
            self,
            agent_runtime_endpoint_id,
            agent_runtime_id=agent_core_runtime.attr_agent_runtime_id,
            agent_runtime_version=agentcore_runtime_version,
            name="dev",
        )

        # stack outputs
        cdk.CfnOutput(
            self,
            f"{docker_asset_id}ImageUri",
            value=docker_asset.image_uri,
            description="Docker asset image URI",
            export_name=f"{docker_asset_id}ImageUri",
        )

        cdk.CfnOutput(
            self,
            f"{agent_runtime_id}Id",
            value=agent_core_runtime.attr_agent_runtime_id,
            description="Agent runtime ID",
            export_name=f"{agent_runtime_id}Id",
        )

        cdk.CfnOutput(
            self,
            f"{agent_runtime_id}Arn",
            value=agent_core_runtime.attr_agent_runtime_arn,
            description="Agent runtime ARN",
            export_name=f"{agent_runtime_id}Arn",
        )

        cdk.CfnOutput(
            self,
            f"{iam_role_id}Arn",
            value=runtime_role.role_arn,
            description="Agent Runtime role ARN",
            export_name=f"{iam_role_id}Arn",
        )
