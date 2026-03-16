import aws_cdk as cdk
from aws_cdk import aws_cognito as cognito
from constructs import Construct


class DeepAgentCognito(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_pool_id = f"{construct_id}UserPool"
        user_pool_client_id = f"{construct_id}UserPoolClient"
        user_pool_domain_id = f"{construct_id}UserPoolDomain"
        resource_server_id = f"{construct_id}ResourceServer"

        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            user_pool_id,
            user_pool_name=user_pool_id,
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Cognito User Pool Domain
        self.user_pool_domain = self.user_pool.add_domain(
            user_pool_domain_id,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=cdk.Fn.join(
                    "-",
                    [
                        "deep-agent",
                        cdk.Aws.ACCOUNT_ID,
                        cdk.Aws.REGION,
                    ],
                ),
            ),
        )

        # Cognito Resource Server
        invoke_scope = cognito.ResourceServerScope(
            scope_name="invoke",
            scope_description="Invoke the deep agent",
        )

        self.resource_server = self.user_pool.add_resource_server(
            resource_server_id,
            identifier="deepagent",
            scopes=[invoke_scope],
        )

        # Cognito User Pool Client
        self.user_pool_client = self.user_pool.add_client(
            user_pool_client_id,
            user_pool_client_name=user_pool_client_id,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=False,
                ),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                    cognito.OAuthScope.resource_server(self.resource_server, invoke_scope),
                ],
            ),
            prevent_user_existence_errors=True,
            generate_secret=False,
            id_token_validity=cdk.Duration.hours(1),
            access_token_validity=cdk.Duration.hours(1),
            refresh_token_validity=cdk.Duration.days(30),
        )

        # Stack outputs
        cdk.CfnOutput(
            self,
            f"{user_pool_id}Id",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID",
            export_name=f"{user_pool_id}Id",
        )

        cdk.CfnOutput(
            self,
            f"{user_pool_id}Arn",
            value=self.user_pool.user_pool_arn,
            description="Cognito User Pool ARN",
            export_name=f"{user_pool_id}Arn",
        )

        cdk.CfnOutput(
            self,
            f"{user_pool_client_id}Id",
            value=self.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
            export_name=f"{user_pool_client_id}Id",
        )

        cdk.CfnOutput(
            self,
            f"{user_pool_domain_id}Name",
            value=self.user_pool_domain.domain_name,
            description="Cognito User Pool Domain name",
            export_name=f"{user_pool_domain_id}Name",
        )

        cdk.CfnOutput(
            self,
            f"{user_pool_domain_id}BaseUrl",
            value=self.user_pool_domain.base_url(),
            description="Cognito User Pool Domain base URL",
            export_name=f"{user_pool_domain_id}BaseUrl",
        )

        cdk.CfnOutput(
            self,
            f"{resource_server_id}Identifier",
            value=self.resource_server.user_pool_resource_server_id,
            description="Cognito Resource Server identifier",
            export_name=f"{resource_server_id}Identifier",
        )
