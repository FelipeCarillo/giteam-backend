import json
import logging
from datetime import datetime, UTC

from sqlalchemy import and_

from infra.database import Database
from helpers.enums import AgentFunction
from agent.github_ai_agent import GitHubAIAgent
from models.models import Repository, Operation as OperationORM, CostHistory as CostHistoryORM, ProviderSecretKey

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler para processar eventos do GitHub via SQS
    """

    logger.info(f"Received event: {json.dumps(event)}")

    db = Database()
    session = db.get_session()

    try:
        sqs_message = json.loads(event['Records'][0]['body'])
        github_event = sqs_message['body']

        repository = session.query(Repository).filter(
            and_(
                Repository.id == github_event['repository']['id'],
                Repository.deleted.is_(False)
            )
        ).first()

        if not repository:
            logger.error(f"Repository with ID {github_event['repository']['id']} not found or deleted.")
            return {"statusCode": 404, "body": "Repository not found"}

        event_type = "pull_request" if 'pull_request' in github_event else \
            "issues" if 'issue' in github_event else \
                "issue_comment" if 'comment' in github_event else \
                    'unknown'
        if event_type not in ['pull_request', 'issues', 'issue_comment']:
            logger.error(f"Unsupported event type: {event_type}")
            return {"statusCode": 400, "body": "Unsupported event type"}

        agent = None
        if event_type == 'pull_request':
            if github_event.get('action') not in ['opened', 'edited', 'reopened', 'synchronize']:
                logger.warning(f"Unsupported pull request action: {github_event.get('action')}")
                return {"statusCode": 422, "body": "Action ignored"}

            for ag in repository.agents:
                if ag.function in [AgentFunction.PR_REVIEW, AgentFunction.BOTH] and not ag.deleted:
                    agent = ag
                    break

        else:
            if github_event.get('action') not in ['opened', 'edited', 'reopened']:
                logger.warning(f"Unsupported issue action: {github_event.get('action')}")
                return {"statusCode": 422, "body": "Action ignored"}

            for ag in repository.agents:
                if ag.function in [AgentFunction.ISSUE_RESOLUTION, AgentFunction.BOTH] and not ag.deleted:
                    agent = ag
                    break

        if not agent:
            logger.error(f"No active agent found for {event_type}")
            return {"statusCode": 422, "body": "No agent configured"}

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

        operation = github_agent.process_github_event(github_event, agent)

        if operation:
            today = datetime.now(UTC)
            current_year = today.year
            current_month = today.month
            month = f"{current_year}-{current_month:02d}"

            cost_history = session.query(CostHistoryORM).filter(
                CostHistoryORM.user_id == user.id,
                CostHistoryORM.month == month
            ).first()
            if not cost_history:
                payload = {
                    'user_id': user.id,
                    'month': month,
                    'total_cost': operation.cost
                }
                if github_event.get('event_type') == 'pull_request':
                    payload['pr_cost'] = operation.cost
                else:
                    payload['issue_cost'] = operation.cost

                cost_history = CostHistoryORM(**payload)
                session.add(cost_history)
            else:
                if github_event.get('event_type') == 'pull_request':
                    cost_history.pr_cost += operation.cost
                else:
                    cost_history.issue_cost += operation.cost
                cost_history.total_cost += operation.cost
            session.commit()
            logger.info(f"Cost history updated for user {user.id} for month {month}")

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


if __name__ == '__main__':
    event = {
        "Records": [
            {
                "messageId": "cd5a20e9-14ea-4e4e-a089-f0678e7ac3fa",
                "receiptHandle": "AQEBMzvnxXXGeLEhf0XaGK4KcWsIqrH06G03JYt+DrgYHdx74JHu0Ab1hudd7wOKKJHs3wvedjjjSuG3de2F/rwYEwyVhmMy8W59pXU/imjbVLDqVzVK4LERfhHVSNINbkX9bR0yVeuB7g7E+qIzpMcAC6jHplkFG5+YiZUTODOzasL2tdW42MAtidLCS7JDOiMet85HQ1zPoa91E5kId4lXfrxmTEmJNvaQ68ApVqr4u8QOalAFiwR3q2jUPbGI1y9ULtqwMf/hxRi9tvY42GF4h+UZzMq1TG3tQUk18f1e0sqnKY3zz+aQuWhQX5PqaTM2WYDzQ+JTY4ew+fyORaik4LRba2BUDv3wrGFw68q4WicZk5qRlQT7tDWYL66b/IPwfwBjFj3Yz1gdN8ziqcAbNg==",
                "body": "{\"body\": {\"action\": \"reopened\", \"number\": 1, \"pull_request\": {\"url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1\", \"id\": 2589078665, \"node_id\": \"PR_kwDOONKdKM6aUjSJ\", \"html_url\": \"https://github.com/FelipeCarillo/agente-corretor/pull/1\", \"diff_url\": \"https://github.com/FelipeCarillo/agente-corretor/pull/1.diff\", \"patch_url\": \"https://github.com/FelipeCarillo/agente-corretor/pull/1.patch\", \"issue_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/1\", \"number\": 1, \"state\": \"closed\", \"locked\": false, \"title\": \"Update README.md\", \"user\": {\"login\": \"FelipeCarillo\", \"id\": 63021830, \"node_id\": \"MDQ6VXNlcjYzMDIxODMw\", \"avatar_url\": \"https://avatars.githubusercontent.com/u/63021830?v=4\", \"gravatar_id\": \"\", \"url\": \"https://api.github.com/users/FelipeCarillo\", \"html_url\": \"https://github.com/FelipeCarillo\", \"followers_url\": \"https://api.github.com/users/FelipeCarillo/followers\", \"following_url\": \"https://api.github.com/users/FelipeCarillo/following{/other_user}\", \"gists_url\": \"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\", \"starred_url\": \"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\", \"subscriptions_url\": \"https://api.github.com/users/FelipeCarillo/subscriptions\", \"organizations_url\": \"https://api.github.com/users/FelipeCarillo/orgs\", \"repos_url\": \"https://api.github.com/users/FelipeCarillo/repos\", \"events_url\": \"https://api.github.com/users/FelipeCarillo/events{/privacy}\", \"received_events_url\": \"https://api.github.com/users/FelipeCarillo/received_events\", \"type\": \"User\", \"user_view_type\": \"public\", \"site_admin\": false}, \"body\": null, \"created_at\": \"2025-06-13T04:41:04Z\", \"updated_at\": \"2025-06-13T06:51:36Z\", \"closed_at\": \"2025-06-13T06:51:36Z\", \"merged_at\": null, \"merge_commit_sha\": \"ffd7753e7a5edc9118e99385ad2354762b688708\", \"assignee\": null, \"assignees\": [], \"requested_reviewers\": [], \"requested_teams\": [], \"labels\": [], \"milestone\": null, \"draft\": false, \"commits_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1/commits\", \"review_comments_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1/comments\", \"review_comment_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/comments{/number}\", \"comments_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/1/comments\", \"statuses_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/100ba89359e5ca61f16c12ec49bf0dd3be77f3f6\", \"head\": {\"label\": \"FelipeCarillo:teste\", \"ref\": \"teste\", \"sha\": \"100ba89359e5ca61f16c12ec49bf0dd3be77f3f6\", \"user\": {\"login\": \"FelipeCarillo\", \"id\": 63021830, \"node_id\": \"MDQ6VXNlcjYzMDIxODMw\", \"avatar_url\": \"https://avatars.githubusercontent.com/u/63021830?v=4\", \"gravatar_id\": \"\", \"url\": \"https://api.github.com/users/FelipeCarillo\", \"html_url\": \"https://github.com/FelipeCarillo\", \"followers_url\": \"https://api.github.com/users/FelipeCarillo/followers\", \"following_url\": \"https://api.github.com/users/FelipeCarillo/following{/other_user}\", \"gists_url\": \"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\", \"starred_url\": \"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\", \"subscriptions_url\": \"https://api.github.com/users/FelipeCarillo/subscriptions\", \"organizations_url\": \"https://api.github.com/users/FelipeCarillo/orgs\", \"repos_url\": \"https://api.github.com/users/FelipeCarillo/repos\", \"events_url\": \"https://api.github.com/users/FelipeCarillo/events{/privacy}\", \"received_events_url\": \"https://api.github.com/users/FelipeCarillo/received_events\", \"type\": \"User\", \"user_view_type\": \"public\", \"site_admin\": false}, \"repo\": {\"id\": 953326888, \"node_id\": \"R_kgDOONKdKA\", \"name\": \"agente-corretor\", \"full_name\": \"FelipeCarillo/agente-corretor\", \"private\": true, \"owner\": {\"login\": \"FelipeCarillo\", \"id\": 63021830, \"node_id\": \"MDQ6VXNlcjYzMDIxODMw\", \"avatar_url\": \"https://avatars.githubusercontent.com/u/63021830?v=4\", \"gravatar_id\": \"\", \"url\": \"https://api.github.com/users/FelipeCarillo\", \"html_url\": \"https://github.com/FelipeCarillo\", \"followers_url\": \"https://api.github.com/users/FelipeCarillo/followers\", \"following_url\": \"https://api.github.com/users/FelipeCarillo/following{/other_user}\", \"gists_url\": \"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\", \"starred_url\": \"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\", \"subscriptions_url\": \"https://api.github.com/users/FelipeCarillo/subscriptions\", \"organizations_url\": \"https://api.github.com/users/FelipeCarillo/orgs\", \"repos_url\": \"https://api.github.com/users/FelipeCarillo/repos\", \"events_url\": \"https://api.github.com/users/FelipeCarillo/events{/privacy}\", \"received_events_url\": \"https://api.github.com/users/FelipeCarillo/received_events\", \"type\": \"User\", \"user_view_type\": \"public\", \"site_admin\": false}, \"html_url\": \"https://github.com/FelipeCarillo/agente-corretor\", \"description\": null, \"fork\": false, \"url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor\", \"forks_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/forks\", \"keys_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/keys{/key_id}\", \"collaborators_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/collaborators{/collaborator}\", \"teams_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/teams\", \"hooks_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/hooks\", \"issue_events_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/events{/number}\", \"events_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/events\", \"assignees_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/assignees{/user}\", \"branches_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/branches{/branch}\", \"tags_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/tags\", \"blobs_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/blobs{/sha}\", \"git_tags_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/tags{/sha}\", \"git_refs_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/refs{/sha}\", \"trees_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/trees{/sha}\", \"statuses_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/{sha}\", \"languages_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/languages\", \"stargazers_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/stargazers\", \"contributors_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/contributors\", \"subscribers_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscribers\", \"subscription_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscription\", \"commits_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/commits{/sha}\", \"git_commits_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/commits{/sha}\", \"comments_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/comments{/number}\", \"issue_comment_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/comments{/number}\", \"contents_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/contents/{+path}\", \"compare_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/compare/{base}...{head}\", \"merges_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/merges\", \"archive_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/{archive_format}{/ref}\", \"downloads_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/downloads\", \"issues_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues{/number}\", \"pulls_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls{/number}\", \"milestones_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/milestones{/number}\", \"notifications_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/notifications{?since,all,participating}\", \"labels_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/labels{/name}\", \"releases_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/releases{/id}\", \"deployments_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/deployments\", \"created_at\": \"2025-03-23T05:00:35Z\", \"updated_at\": \"2025-03-23T05:00:39Z\", \"pushed_at\": \"2025-06-13T04:40:57Z\", \"git_url\": \"git://github.com/FelipeCarillo/agente-corretor.git\", \"ssh_url\": \"git@github.com:FelipeCarillo/agente-corretor.git\", \"clone_url\": \"https://github.com/FelipeCarillo/agente-corretor.git\", \"svn_url\": \"https://github.com/FelipeCarillo/agente-corretor\", \"homepage\": null, \"size\": 1, \"stargazers_count\": 0, \"watchers_count\": 0, \"language\": null, \"has_issues\": true, \"has_projects\": true, \"has_downloads\": true, \"has_wiki\": true, \"has_pages\": false, \"has_discussions\": false, \"forks_count\": 0, \"mirror_url\": null, \"archived\": false, \"disabled\": false, \"open_issues_count\": 0, \"license\": null, \"allow_forking\": true, \"is_template\": false, \"web_commit_signoff_required\": false, \"topics\": [], \"visibility\": \"private\", \"forks\": 0, \"open_issues\": 0, \"watchers\": 0, \"default_branch\": \"main\", \"allow_squash_merge\": true, \"allow_merge_commit\": true, \"allow_rebase_merge\": true, \"allow_auto_merge\": false, \"delete_branch_on_merge\": false, \"allow_update_branch\": false, \"use_squash_pr_title_as_default\": false, \"squash_merge_commit_message\": \"COMMIT_MESSAGES\", \"squash_merge_commit_title\": \"COMMIT_OR_PR_TITLE\", \"merge_commit_message\": \"PR_TITLE\", \"merge_commit_title\": \"MERGE_MESSAGE\"}}, \"base\": {\"label\": \"FelipeCarillo:main\", \"ref\": \"main\", \"sha\": \"d3e70f098e40b6cdb9d0a2bf6e42cd6b618770d8\", \"user\": {\"login\": \"FelipeCarillo\", \"id\": 63021830, \"node_id\": \"MDQ6VXNlcjYzMDIxODMw\", \"avatar_url\": \"https://avatars.githubusercontent.com/u/63021830?v=4\", \"gravatar_id\": \"\", \"url\": \"https://api.github.com/users/FelipeCarillo\", \"html_url\": \"https://github.com/FelipeCarillo\", \"followers_url\": \"https://api.github.com/users/FelipeCarillo/followers\", \"following_url\": \"https://api.github.com/users/FelipeCarillo/following{/other_user}\", \"gists_url\": \"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\", \"starred_url\": \"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\", \"subscriptions_url\": \"https://api.github.com/users/FelipeCarillo/subscriptions\", \"organizations_url\": \"https://api.github.com/users/FelipeCarillo/orgs\", \"repos_url\": \"https://api.github.com/users/FelipeCarillo/repos\", \"events_url\": \"https://api.github.com/users/FelipeCarillo/events{/privacy}\", \"received_events_url\": \"https://api.github.com/users/FelipeCarillo/received_events\", \"type\": \"User\", \"user_view_type\": \"public\", \"site_admin\": false}, \"repo\": {\"id\": 953326888, \"node_id\": \"R_kgDOONKdKA\", \"name\": \"agente-corretor\", \"full_name\": \"FelipeCarillo/agente-corretor\", \"private\": true, \"owner\": {\"login\": \"FelipeCarillo\", \"id\": 63021830, \"node_id\": \"MDQ6VXNlcjYzMDIxODMw\", \"avatar_url\": \"https://avatars.githubusercontent.com/u/63021830?v=4\", \"gravatar_id\": \"\", \"url\": \"https://api.github.com/users/FelipeCarillo\", \"html_url\": \"https://github.com/FelipeCarillo\", \"followers_url\": \"https://api.github.com/users/FelipeCarillo/followers\", \"following_url\": \"https://api.github.com/users/FelipeCarillo/following{/other_user}\", \"gists_url\": \"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\", \"starred_url\": \"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\", \"subscriptions_url\": \"https://api.github.com/users/FelipeCarillo/subscriptions\", \"organizations_url\": \"https://api.github.com/users/FelipeCarillo/orgs\", \"repos_url\": \"https://api.github.com/users/FelipeCarillo/repos\", \"events_url\": \"https://api.github.com/users/FelipeCarillo/events{/privacy}\", \"received_events_url\": \"https://api.github.com/users/FelipeCarillo/received_events\", \"type\": \"User\", \"user_view_type\": \"public\", \"site_admin\": false}, \"html_url\": \"https://github.com/FelipeCarillo/agente-corretor\", \"description\": null, \"fork\": false, \"url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor\", \"forks_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/forks\", \"keys_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/keys{/key_id}\", \"collaborators_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/collaborators{/collaborator}\", \"teams_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/teams\", \"hooks_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/hooks\", \"issue_events_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/events{/number}\", \"events_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/events\", \"assignees_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/assignees{/user}\", \"branches_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/branches{/branch}\", \"tags_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/tags\", \"blobs_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/blobs{/sha}\", \"git_tags_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/tags{/sha}\", \"git_refs_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/refs{/sha}\", \"trees_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/trees{/sha}\", \"statuses_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/{sha}\", \"languages_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/languages\", \"stargazers_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/stargazers\", \"contributors_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/contributors\", \"subscribers_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscribers\", \"subscription_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscription\", \"commits_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/commits{/sha}\", \"git_commits_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/commits{/sha}\", \"comments_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/comments{/number}\", \"issue_comment_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/comments{/number}\", \"contents_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/contents/{+path}\", \"compare_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/compare/{base}...{head}\", \"merges_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/merges\", \"archive_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/{archive_format}{/ref}\", \"downloads_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/downloads\", \"issues_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues{/number}\", \"pulls_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls{/number}\", \"milestones_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/milestones{/number}\", \"notifications_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/notifications{?since,all,participating}\", \"labels_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/labels{/name}\", \"releases_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/releases{/id}\", \"deployments_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/deployments\", \"created_at\": \"2025-03-23T05:00:35Z\", \"updated_at\": \"2025-03-23T05:00:39Z\", \"pushed_at\": \"2025-06-13T04:40:57Z\", \"git_url\": \"git://github.com/FelipeCarillo/agente-corretor.git\", \"ssh_url\": \"git@github.com:FelipeCarillo/agente-corretor.git\", \"clone_url\": \"https://github.com/FelipeCarillo/agente-corretor.git\", \"svn_url\": \"https://github.com/FelipeCarillo/agente-corretor\", \"homepage\": null, \"size\": 1, \"stargazers_count\": 0, \"watchers_count\": 0, \"language\": null, \"has_issues\": true, \"has_projects\": true, \"has_downloads\": true, \"has_wiki\": true, \"has_pages\": false, \"has_discussions\": false, \"forks_count\": 0, \"mirror_url\": null, \"archived\": false, \"disabled\": false, \"open_issues_count\": 0, \"license\": null, \"allow_forking\": true, \"is_template\": false, \"web_commit_signoff_required\": false, \"topics\": [], \"visibility\": \"private\", \"forks\": 0, \"open_issues\": 0, \"watchers\": 0, \"default_branch\": \"main\", \"allow_squash_merge\": true, \"allow_merge_commit\": true, \"allow_rebase_merge\": true, \"allow_auto_merge\": false, \"delete_branch_on_merge\": false, \"allow_update_branch\": false, \"use_squash_pr_title_as_default\": false, \"squash_merge_commit_message\": \"COMMIT_MESSAGES\", \"squash_merge_commit_title\": \"COMMIT_OR_PR_TITLE\", \"merge_commit_message\": \"PR_TITLE\", \"merge_commit_title\": \"MERGE_MESSAGE\"}}, \"_links\": {\"self\": {\"href\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1\"}, \"html\": {\"href\": \"https://github.com/FelipeCarillo/agente-corretor/pull/1\"}, \"issue\": {\"href\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/1\"}, \"comments\": {\"href\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/1/comments\"}, \"review_comments\": {\"href\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1/comments\"}, \"review_comment\": {\"href\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/comments{/number}\"}, \"commits\": {\"href\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1/commits\"}, \"statuses\": {\"href\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/100ba89359e5ca61f16c12ec49bf0dd3be77f3f6\"}}, \"author_association\": \"OWNER\", \"auto_merge\": null, \"active_lock_reason\": null, \"merged\": false, \"mergeable\": true, \"rebaseable\": false, \"mergeable_state\": \"clean\", \"merged_by\": null, \"comments\": 0, \"review_comments\": 0, \"maintainer_can_modify\": false, \"commits\": 1, \"additions\": 3, \"deletions\": 1, \"changed_files\": 1}, \"repository\": {\"id\": 953326888, \"node_id\": \"R_kgDOONKdKA\", \"name\": \"agente-corretor\", \"full_name\": \"FelipeCarillo/agente-corretor\", \"private\": true, \"owner\": {\"login\": \"FelipeCarillo\", \"id\": 63021830, \"node_id\": \"MDQ6VXNlcjYzMDIxODMw\", \"avatar_url\": \"https://avatars.githubusercontent.com/u/63021830?v=4\", \"gravatar_id\": \"\", \"url\": \"https://api.github.com/users/FelipeCarillo\", \"html_url\": \"https://github.com/FelipeCarillo\", \"followers_url\": \"https://api.github.com/users/FelipeCarillo/followers\", \"following_url\": \"https://api.github.com/users/FelipeCarillo/following{/other_user}\", \"gists_url\": \"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\", \"starred_url\": \"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\", \"subscriptions_url\": \"https://api.github.com/users/FelipeCarillo/subscriptions\", \"organizations_url\": \"https://api.github.com/users/FelipeCarillo/orgs\", \"repos_url\": \"https://api.github.com/users/FelipeCarillo/repos\", \"events_url\": \"https://api.github.com/users/FelipeCarillo/events{/privacy}\", \"received_events_url\": \"https://api.github.com/users/FelipeCarillo/received_events\", \"type\": \"User\", \"user_view_type\": \"public\", \"site_admin\": false}, \"html_url\": \"https://github.com/FelipeCarillo/agente-corretor\", \"description\": null, \"fork\": false, \"url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor\", \"forks_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/forks\", \"keys_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/keys{/key_id}\", \"collaborators_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/collaborators{/collaborator}\", \"teams_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/teams\", \"hooks_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/hooks\", \"issue_events_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/events{/number}\", \"events_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/events\", \"assignees_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/assignees{/user}\", \"branches_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/branches{/branch}\", \"tags_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/tags\", \"blobs_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/blobs{/sha}\", \"git_tags_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/tags{/sha}\", \"git_refs_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/refs{/sha}\", \"trees_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/trees{/sha}\", \"statuses_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/{sha}\", \"languages_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/languages\", \"stargazers_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/stargazers\", \"contributors_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/contributors\", \"subscribers_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscribers\", \"subscription_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscription\", \"commits_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/commits{/sha}\", \"git_commits_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/commits{/sha}\", \"comments_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/comments{/number}\", \"issue_comment_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/comments{/number}\", \"contents_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/contents/{+path}\", \"compare_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/compare/{base}...{head}\", \"merges_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/merges\", \"archive_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/{archive_format}{/ref}\", \"downloads_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/downloads\", \"issues_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues{/number}\", \"pulls_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls{/number}\", \"milestones_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/milestones{/number}\", \"notifications_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/notifications{?since,all,participating}\", \"labels_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/labels{/name}\", \"releases_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/releases{/id}\", \"deployments_url\": \"https://api.github.com/repos/FelipeCarillo/agente-corretor/deployments\", \"created_at\": \"2025-03-23T05:00:35Z\", \"updated_at\": \"2025-03-23T05:00:39Z\", \"pushed_at\": \"2025-06-13T04:40:57Z\", \"git_url\": \"git://github.com/FelipeCarillo/agente-corretor.git\", \"ssh_url\": \"git@github.com:FelipeCarillo/agente-corretor.git\", \"clone_url\": \"https://github.com/FelipeCarillo/agente-corretor.git\", \"svn_url\": \"https://github.com/FelipeCarillo/agente-corretor\", \"homepage\": null, \"size\": 1, \"stargazers_count\": 0, \"watchers_count\": 0, \"language\": null, \"has_issues\": true, \"has_projects\": true, \"has_downloads\": true, \"has_wiki\": true, \"has_pages\": false, \"has_discussions\": false, \"forks_count\": 0, \"mirror_url\": null, \"archived\": false, \"disabled\": false, \"open_issues_count\": 0, \"license\": null, \"allow_forking\": true, \"is_template\": false, \"web_commit_signoff_required\": false, \"topics\": [], \"visibility\": \"private\", \"forks\": 0, \"open_issues\": 0, \"watchers\": 0, \"default_branch\": \"main\"}, \"sender\": {\"login\": \"FelipeCarillo\", \"id\": 63021830, \"node_id\": \"MDQ6VXNlcjYzMDIxODMw\", \"avatar_url\": \"https://avatars.githubusercontent.com/u/63021830?v=4\", \"gravatar_id\": \"\", \"url\": \"https://api.github.com/users/FelipeCarillo\", \"html_url\": \"https://github.com/FelipeCarillo\", \"followers_url\": \"https://api.github.com/users/FelipeCarillo/followers\", \"following_url\": \"https://api.github.com/users/FelipeCarillo/following{/other_user}\", \"gists_url\": \"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\", \"starred_url\": \"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\", \"subscriptions_url\": \"https://api.github.com/users/FelipeCarillo/subscriptions\", \"organizations_url\": \"https://api.github.com/users/FelipeCarillo/orgs\", \"repos_url\": \"https://api.github.com/users/FelipeCarillo/repos\", \"events_url\": \"https://api.github.com/users/FelipeCarillo/events{/privacy}\", \"received_events_url\": \"https://api.github.com/users/FelipeCarillo/received_events\", \"type\": \"User\", \"user_view_type\": \"public\", \"site_admin\": false}}, \"headers\": {\"Accept\": \"*/*\", \"CloudFront-Forwarded-Proto\": \"https\", \"CloudFront-Is-Desktop-Viewer\": \"true\", \"CloudFront-Is-Mobile-Viewer\": \"false\", \"CloudFront-Is-SmartTV-Viewer\": \"false\", \"CloudFront-Is-Tablet-Viewer\": \"false\", \"CloudFront-Viewer-ASN\": \"36459\", \"CloudFront-Viewer-Country\": \"US\", \"Content-Type\": \"application/json\", \"Host\": \"xkqzt118zj.execute-api.sa-east-1.amazonaws.com\", \"User-Agent\": \"GitHub-Hookshot/fb6e15e\", \"Via\": \"1.1 67e0252f80139a17537e71117acd6be0.cloudfront.net (CloudFront)\", \"X-Amz-Cf-Id\": \"41YQfBag940ilPDtI67FVpGyHleuTTY514Ztvb2YupySYmcS0oiJRg==\", \"X-Amzn-Trace-Id\": \"Root=1-684bca79-737eda146db079dd790ebe9f\", \"X-Forwarded-For\": \"140.82.115.42, 15.158.60.169\", \"X-Forwarded-Port\": \"443\", \"X-Forwarded-Proto\": \"https\", \"X-GitHub-Delivery\": \"d9ca7f20-4822-11f0-8059-6a12b76f4f19\", \"X-GitHub-Event\": \"pull_request\", \"X-GitHub-Hook-ID\": \"552009075\", \"X-GitHub-Hook-Installation-Target-ID\": \"953326888\", \"X-GitHub-Hook-Installation-Target-Type\": \"repository\", \"X-Hub-Signature\": \"sha1=ba2ec943f6076c3d2a0522724d413ffbe1094c90\", \"X-Hub-Signature-256\": \"sha256=d516fa043070ca5e2cbea741f4ccb4758113ebcca4e882975943af167f54d81d\"}, \"timestamp\": \"62424869-dad9-4d1a-b2dc-3227b53b58a7\"}",
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "AWSTraceHeader": "Root=1-684bca79-737eda146db079dd790ebe9f;Parent=725373302ba4d218;Sampled=0;Lineage=1:03e79db1:0",
                    "SentTimestamp": "1749797506671",
                    "SenderId": "AROA2EOYBP775YWWVRGED:GiteamStack-GitTeamsWebHookLambdaD12DA964-znOqntrM1n7L",
                    "ApproximateFirstReceiveTimestamp": "1749797506681"
                },
                "messageAttributes": {},
                "md5OfBody": "43da29a50a0ee6cb47851494a58c3148",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:sa-east-1:696774655999:GitTeamsAgentQueue",
                "awsRegion": "sa-east-1"
            }
        ]
    }

    lambda_handler(event, None)
