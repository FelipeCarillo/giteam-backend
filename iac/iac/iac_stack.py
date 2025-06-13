import os
import dotenv

dotenv.load_dotenv()

from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_lambda_event_sources as lambda_event_sources,
)
from constructs import Construct


class IacStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api = apigateway.RestApi(
            self,
            "GitTeamsApi",
            rest_api_name="GitTeams Service",
            description="This service serves GitTeams.",
            default_cors_preflight_options={
                "allow_origins": apigateway.Cors.ALL_ORIGINS,
                "allow_methods": apigateway.Cors.ALL_METHODS,
            }
        )

        queue = sqs.Queue(
            self,
            "GitTeamsAgentQueue",
            queue_name="GitTeamsAgentQueue",
            visibility_timeout=Duration.seconds(30)
        )

        github_agent = _lambda.Function(
            self,
            "GitTeamsAgentLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="webhooks.github_agent.lambda_handler",
            code=_lambda.Code.from_asset("app"),
            timeout=Duration.seconds(30),
            environment={
                "DATABASE_URL": os.getenv("DATABASE_URL"),
                "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
            }
        )
        github_webhook = _lambda.Function(
            self,
            "GitTeamsWebHookLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="webhooks.github_webhook.lambda_handler",
            code=_lambda.Code.from_asset("app"),
            timeout=Duration.seconds(30),
            environment={
                "DATABASE_URL": os.getenv("DATABASE_URL"),
                "QUEUE_URL": queue.queue_url
            }
        )

        api.root.add_resource("api").add_resource("github").add_resource(
            "webhook",
            default_cors_preflight_options={
                "allow_origins": apigateway.Cors.ALL_ORIGINS,
                "allow_methods": apigateway.Cors.ALL_METHODS,
                "allow_headers": apigateway.Cors.DEFAULT_HEADERS,
            }
        ).add_method(
            "POST",
            apigateway.LambdaIntegration(github_webhook)
        )

        github_agent.add_event_source(lambda_event_sources.SqsEventSource(queue))
        queue.grant_send_messages(github_webhook)
        queue.grant_consume_messages(github_agent)
