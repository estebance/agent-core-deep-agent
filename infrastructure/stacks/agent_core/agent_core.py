import os

import aws_cdk as cdk
import aws_cdk.aws_ecr_assets as ecr_assets
from aws_cdk import (
    aws_bedrockagentcore as agentcore,
)
from aws_cdk import (
    aws_ecr as ecr,
)
from aws_cdk import aws_iam as iam
from constructs import Construct


class DeepAgentCore(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        region = cdk.Stack.of(self).region
        account_id = cdk.Stack.of(self).account

        # ecr_repo_id = f"{construct_id}-ecr"
        docker_asset_id = f"{construct_id}DockerAsset"
        agent_runtime_id = f"{construct_id}AgentRuntime"
        agent_runtime_endpoint_id = f"{construct_id}AgentRuntimeEndpoint"
        iam_role_id = f"{construct_id}AgtcoreRole"

        asset = ecr_assets.DockerImageAsset(
            self, docker_asset_id, directory=os.path.join(os.getcwd())
        )

        # repository = ecr.Repository(self, ecr_repo_id, repository_name=ecr_repo_id)
        agentcore_runtime_version = kwargs.get("agentcore_runtime_version", "1")
        # The runtime by default create ECR permission only for the repository available in the account the stack is being deployed
        agent_runtime_artifact = agentcore.CfnRuntime.AgentRuntimeArtifactProperty(
            container_configuration=agentcore.CfnRuntime.ContainerConfigurationProperty(
                container_uri=asset.image_uri
            )
        )

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

        agent_core_runtime = agentcore.CfnRuntime(
            self,
            agent_runtime_id,
            agent_runtime_artifact=agent_runtime_artifact,
            agent_runtime_name=agent_runtime_id,
            protocol_configuration="HTTP",
            network_configuration=agentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC"
            ),
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

        # CHECK this
        # bedrockagentcore.CfnRuntimeEndpoint(
        #     self,
        #     f"{props.app_name}-AgentCoreRuntimeDevEndpoint",
        #     agent_runtime_id=self.agent_core_runtime.attr_agent_runtime_id,
        #     agent_runtime_version="1",
        #     name="DEV",
        # )
