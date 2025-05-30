import json

from helpers.enums import AgentFunction
from infra.database import Database
from agent.github_ai_agent import GitHubAIAgent
from models.models import Repository, RepositoryWebhook, Agent


async def lambda_handler(event, context):
    sqs_message = json.loads(event['Records'][0]['body'])
    github_event = json.loads(sqs_message['Message'])

    db = Database()
    session = db.get_session()

    repository = session.query(Repository).filter(
        Repository.id == github_event['repository']['id'] and
        Repository.deleted.is_(False)
    ).first()
    if not repository:
        print(f"Repository with ID {github_event['repository']['id']} not found or deleted.")
        return

    event_type = github_event.get('event_type', 'unknown')
    branches_names = [branch.name for branch in repository.branches]
    if event_type not in ['pull_request', 'issue', 'issue_comment']:
        print(f"Unsupported event type: {event_type}")
        return
    if event_type == 'pull_request':
        if github_event['action'] not in ['opened', 'edited', 'closed']:
            print(f"Unsupported pull request action: {github_event['action']}")
            return
        if github_event['branch'] not in branches_names:
            print(f"Branch {github_event['branch']} not found in repository branches.")
            return
        agent = repository.agents.filter(
            Agent.function == AgentFunction.PR_REVIEW or
            Agent.function == AgentFunction.BOTH,
        ).first()
    else:
        if github_event['action'] not in ['opened', 'edited', 'closed']:
            print(f"Unsupported issue action: {github_event['action']}")
            return
        agent = repository.agents.filter(
            Agent.function == AgentFunction.ISSUE_RESOLUTION or
            Agent.function == AgentFunction.BOTH,
        ).first()

    user = agent.created_by
    openai_api_key = user.settings.openai_api_key if user.settings else None
    anthropic_api_key = user.settings.anthropic_api_key if user.settings else None

    github_agent = GitHubAIAgent(
        github_token=repository.webhooks[0].github_token,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
    )

    operation = await github_agent.process_github_event(github_event, agent)

    save_operation(operation)
