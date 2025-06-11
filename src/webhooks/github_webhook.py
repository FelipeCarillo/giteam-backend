import json
import logging
from sqlalchemy import and_

from infra.database import Database
from helpers.enums import AgentFunction
from models.models import Repository, Agent, Operation as OperationORM, ProviderSecretKey
from agent.github_ai_agent import GitHubAIAgent

logger = logging.getLogger(__name__)


async def lambda_handler(event, context):
    """
    AWS Lambda handler para processar eventos do GitHub via SQS
    """
    db = Database() 
    session = db.get_session()

    try:
        sqs_message = json.loads(event['Records'][0]['body'])
        github_event = json.loads(sqs_message['Message'])

        repository = session.query(Repository).filter(
            and_(
                Repository.id == github_event['repository']['id'],
                Repository.deleted.is_(False)
            )
        ).first()

        if not repository:
            logger.error(f"Repository with ID {github_event['repository']['id']} not found or deleted.")
            return {"statusCode": 404, "body": "Repository not found"}

        event_type = github_event.get('event_type', 'unknown')
        if event_type not in ['pull_request', 'issues', 'issue_comment']:
            logger.error(f"Unsupported event type: {event_type}")
            return {"statusCode": 400, "body": "Unsupported event type"}

        agent = None
        if event_type == 'pull_request':
            if github_event.get('action') not in ['opened', 'edited', 'closed', 'reopened', 'synchronize']:
                logger.warning(f"Unsupported pull request action: {github_event.get('action')}")
                return {"statusCode": 200, "body": "Action ignored"}

            pr_data = github_event.get('pull_request', {})
            target_branch = pr_data.get('base', {}).get('ref')
            branch_names = [branch.name for branch in repository.branches]

            if branch_names and target_branch not in branch_names:
                logger.warning(f"Branch {target_branch} not configured for monitoring.")
                return {"statusCode": 200, "body": "Branch not monitored"}

            for ag in repository.agents:
                if ag.function in [AgentFunction.PR_REVIEW, AgentFunction.BOTH] and not ag.deleted:
                    agent = ag
                    break

        else:
            if github_event.get('action') not in ['opened', 'edited', 'closed', 'reopened']:
                logger.warning(f"Unsupported issue action: {github_event.get('action')}")
                return {"statusCode": 200, "body": "Action ignored"}

            for ag in repository.agents:
                if ag.function in [AgentFunction.ISSUE_RESOLUTION, AgentFunction.BOTH] and not ag.deleted:
                    agent = ag
                    break

        if not agent:
            logger.error(f"No active agent found for {event_type}")
            return {"statusCode": 404, "body": "No agent configured"}

        user = agent.created_by

        openai_key = None
        anthropic_key = None

        provider_keys = session.query(ProviderSecretKey).filter(
            ProviderSecretKey.created_by_id == user.id
        ).all()

        for key in provider_keys:
            if key.provider.value == "OpenAI":
                openai_key = key.secret_key
            elif key.provider.value == "Anthropic":
                anthropic_key = key.secret_key

        import os
        github_token = os.environ.get('GITHUB_TOKEN', '')

        github_agent = GitHubAIAgent(
            github_token=github_token,
            openai_api_key=openai_key,
            anthropic_api_key=anthropic_key,
        )

        github_event['_agent_config'] = {
            'response_length': agent.response_length
        }

        operation = await github_agent.process_github_event(github_event, agent)

        if operation:
            operation_orm = OperationORM(
                agent_id=operation.agent_id,
                action=operation.action,
                details=operation.details,
                github_reference=operation.github_reference,
                prompt_tokens=operation.prompt_tokens,
                completion_tokens=operation.completion_tokens,
                total_tokens=operation.total_tokens,
                cost=operation.cost,
                status=operation.status,
                execution_time=operation.execution_time,
                created_at=operation.created_at
            )
            session.add(operation_orm)
            session.commit()

            logger.info(f"Operation saved successfully: {operation_orm.id}")

        return {"statusCode": 200, "body": "Event processed successfully"}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        session.rollback()
        return {"statusCode": 500, "body": f"Internal error: {str(e)}"}
    finally:
        db.close_session()


# Para executar localmente (não em Lambda)
async def process_github_webhook(payload: dict, github_token: str):
    """
    Processa webhook do GitHub diretamente (sem SQS)
    """
    # Simular estrutura de evento Lambda
    fake_event = {
        'Records': [{
            'body': json.dumps({
                'Message': json.dumps(payload)
            })
        }]
    }

    # Adicionar token ao ambiente temporariamente
    import os
    original_token = os.environ.get('GITHUB_TOKEN')
    os.environ['GITHUB_TOKEN'] = github_token

    try:
        result = await lambda_handler(fake_event, {})
        return result
    finally:
        # Restaurar token original
        if original_token:
            os.environ['GITHUB_TOKEN'] = original_token
        elif 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
