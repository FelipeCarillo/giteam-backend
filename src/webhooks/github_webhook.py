import json
import boto3
import logging
import hmac
import hashlib

from config.env import env
from infra.database import Database
from models import RepositoryWebhook

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')
QUEUE_URL = env.QUEUE_URL


# def verify_github_signature(payload_body, secret_token, signature_header):
#     """Verifica se a assinatura do GitHub é válida"""
#     if not signature_header:
#         return False
#
#     if not signature_header.startswith('sha256='):
#         return False
#
#     expected_signature = 'sha256=' + hmac.new(
#         secret_token.encode('utf-8'),
#         payload_body.encode('utf-8'),
#         hashlib.sha256
#     ).hexdigest()
#
#     return hmac.compare_digest(expected_signature, signature_header)


def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        raw_body = event.get('body', '')
        body = json.loads(raw_body)
        headers = event.get('headers', {})

        # github_signature = headers.get('X-Hub-Signature-256') or headers.get('x-hub-signature-256')

        database = Database()
        session = database.get_session()

        repository_webhook = session.query(RepositoryWebhook).filter(
            RepositoryWebhook.repository_id == body.get('repository', {}).get('id', None)
        ).first()

        if not repository_webhook or repository_webhook.active is False:
            logger.error("Repository webhook not found or inactive.")
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'message': 'Repository webhook not found'
                })
            }

        # if not verify_github_signature(raw_body, repository_webhook.secret, github_signature):
        #     logger.error("Invalid GitHub signature")
        #     return {
        #         'statusCode': 401,
        #         'headers': {
        #             'Content-Type': 'application/json',
        #             'Access-Control-Allow-Origin': '*'
        #         },
        #         'body': json.dumps({
        #             'status': 'error',
        #             'message': 'Invalid signature'
        #         })
        #     }

        message_body = {
            'body': body,
            'headers': headers,
            'timestamp': context.aws_request_id
        }

        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )

        logger.info(f"Message sent to SQS: {response['MessageId']}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token'
            },
            'body': json.dumps({
                'status': 'success',
                'message': 'Webhook received and queued successfully',
                'messageId': response['MessageId']
            })
        }

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }


if __name__ == '__main__':
    event = {
        "resource": "/api/github/webhook",
        "path": "/api/github/webhook",
        "httpMethod": "POST",
        "headers": {
            "Accept": "*/*",
            "CloudFront-Forwarded-Proto": "https",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-Mobile-Viewer": "false",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Tablet-Viewer": "false",
            "CloudFront-Viewer-ASN": "36459",
            "CloudFront-Viewer-Country": "US",
            "Content-Type": "application/json",
            "Host": "xkqzt118zj.execute-api.sa-east-1.amazonaws.com",
            "User-Agent": "GitHub-Hookshot/fb6e15e",
            "Via": "1.1 fa3a5f40cd1a9e910f14498786d64614.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "aWF_qm3ZIH3JibFTAXkUlHcCI4ZTWl93r4-aEtXDEzoayowdk4_56A==",
            "X-Amzn-Trace-Id": "Root=1-684bb49a-45bdd46637e6804164140a01",
            "X-Forwarded-For": "140.82.115.8, 15.158.60.166",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https",
            "X-GitHub-Delivery": "d058a9b0-4815-11f0-9020-82ed0962fc33",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Hook-ID": "552001790",
            "X-GitHub-Hook-Installation-Target-ID": "953326888",
            "X-GitHub-Hook-Installation-Target-Type": "repository",
            "X-Hub-Signature": "sha1=f3e6adf4b303dac4e4c67a91ec7492267c990551",
            "X-Hub-Signature-256": "sha256=89c6cb6865d6d5a384ebd022bfa70278560b51fe8a1ed410f66a36354beb3118"
        },
        "multiValueHeaders": {
            "Accept": [
                "*/*"
            ],
            "CloudFront-Forwarded-Proto": [
                "https"
            ],
            "CloudFront-Is-Desktop-Viewer": [
                "true"
            ],
            "CloudFront-Is-Mobile-Viewer": [
                "false"
            ],
            "CloudFront-Is-SmartTV-Viewer": [
                "false"
            ],
            "CloudFront-Is-Tablet-Viewer": [
                "false"
            ],
            "CloudFront-Viewer-ASN": [
                "36459"
            ],
            "CloudFront-Viewer-Country": [
                "US"
            ],
            "Content-Type": [
                "application/json"
            ],
            "Host": [
                "xkqzt118zj.execute-api.sa-east-1.amazonaws.com"
            ],
            "User-Agent": [
                "GitHub-Hookshot/fb6e15e"
            ],
            "Via": [
                "1.1 fa3a5f40cd1a9e910f14498786d64614.cloudfront.net (CloudFront)"
            ],
            "X-Amz-Cf-Id": [
                "aWF_qm3ZIH3JibFTAXkUlHcCI4ZTWl93r4-aEtXDEzoayowdk4_56A=="
            ],
            "X-Amzn-Trace-Id": [
                "Root=1-684bb49a-45bdd46637e6804164140a01"
            ],
            "X-Forwarded-For": [
                "140.82.115.8, 15.158.60.166"
            ],
            "X-Forwarded-Port": [
                "443"
            ],
            "X-Forwarded-Proto": [
                "https"
            ],
            "X-GitHub-Delivery": [
                "d058a9b0-4815-11f0-9020-82ed0962fc33"
            ],
            "X-GitHub-Event": [
                "pull_request"
            ],
            "X-GitHub-Hook-ID": [
                "552001790"
            ],
            "X-GitHub-Hook-Installation-Target-ID": [
                "953326888"
            ],
            "X-GitHub-Hook-Installation-Target-Type": [
                "repository"
            ],
            "X-Hub-Signature": [
                "sha1=f3e6adf4b303dac4e4c67a91ec7492267c990551"
            ],
            "X-Hub-Signature-256": [
                "sha256=89c6cb6865d6d5a384ebd022bfa70278560b51fe8a1ed410f66a36354beb3118"
            ]
        },
        "queryStringParameters": None,
        "multiValueQueryStringParameters": None,
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "resourceId": "rsh0b8",
            "resourcePath": "/api/github/webhook",
            "httpMethod": "POST",
            "extendedRequestId": "MFkoPEJXmjQEaqg=",
            "requestTime": "13/Jun/2025:05:18:18 +0000",
            "path": "/prod/api/github/webhook",
            "accountId": "696774655999",
            "protocol": "HTTP/1.1",
            "stage": "prod",
            "domainPrefix": "xkqzt118zj",
            "requestTimeEpoch": 1749791898746,
            "requestId": "9191dade-f148-49eb-94e6-ad0ffed7d5b0",
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "sourceIp": "140.82.115.8",
                "principalOrgId": None,
                "accessKey": None,
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "GitHub-Hookshot/fb6e15e",
                "user": None
            },
            "domainName": "xkqzt118zj.execute-api.sa-east-1.amazonaws.com",
            "deploymentId": "uq1nxm",
            "apiId": "xkqzt118zj"
        },
        "body": "{\"action\":\"reopened\",\"number\":1,\"pull_request\":{\"url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1\",\"id\":2589078665,\"node_id\":\"PR_kwDOONKdKM6aUjSJ\",\"html_url\":\"https://github.com/FelipeCarillo/agente-corretor/pull/1\",\"diff_url\":\"https://github.com/FelipeCarillo/agente-corretor/pull/1.diff\",\"patch_url\":\"https://github.com/FelipeCarillo/agente-corretor/pull/1.patch\",\"issue_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/1\",\"number\":1,\"state\":\"open\",\"locked\":false,\"title\":\"Update README.md\",\"user\":{\"login\":\"FelipeCarillo\",\"id\":63021830,\"node_id\":\"MDQ6VXNlcjYzMDIxODMw\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/63021830?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/FelipeCarillo\",\"html_url\":\"https://github.com/FelipeCarillo\",\"followers_url\":\"https://api.github.com/users/FelipeCarillo/followers\",\"following_url\":\"https://api.github.com/users/FelipeCarillo/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/FelipeCarillo/subscriptions\",\"organizations_url\":\"https://api.github.com/users/FelipeCarillo/orgs\",\"repos_url\":\"https://api.github.com/users/FelipeCarillo/repos\",\"events_url\":\"https://api.github.com/users/FelipeCarillo/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/FelipeCarillo/received_events\",\"type\":\"User\",\"user_view_type\":\"public\",\"site_admin\":false},\"body\":null,\"created_at\":\"2025-06-13T04:41:04Z\",\"updated_at\":\"2025-06-13T05:18:17Z\",\"closed_at\":null,\"merged_at\":null,\"merge_commit_sha\":null,\"assignee\":null,\"assignees\":[],\"requested_reviewers\":[],\"requested_teams\":[],\"labels\":[],\"milestone\":null,\"draft\":false,\"commits_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1/commits\",\"review_comments_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1/comments\",\"review_comment_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/comments{/number}\",\"comments_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/1/comments\",\"statuses_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/100ba89359e5ca61f16c12ec49bf0dd3be77f3f6\",\"head\":{\"label\":\"FelipeCarillo:teste\",\"ref\":\"teste\",\"sha\":\"100ba89359e5ca61f16c12ec49bf0dd3be77f3f6\",\"user\":{\"login\":\"FelipeCarillo\",\"id\":63021830,\"node_id\":\"MDQ6VXNlcjYzMDIxODMw\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/63021830?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/FelipeCarillo\",\"html_url\":\"https://github.com/FelipeCarillo\",\"followers_url\":\"https://api.github.com/users/FelipeCarillo/followers\",\"following_url\":\"https://api.github.com/users/FelipeCarillo/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/FelipeCarillo/subscriptions\",\"organizations_url\":\"https://api.github.com/users/FelipeCarillo/orgs\",\"repos_url\":\"https://api.github.com/users/FelipeCarillo/repos\",\"events_url\":\"https://api.github.com/users/FelipeCarillo/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/FelipeCarillo/received_events\",\"type\":\"User\",\"user_view_type\":\"public\",\"site_admin\":false},\"repo\":{\"id\":953326888,\"node_id\":\"R_kgDOONKdKA\",\"name\":\"agente-corretor\",\"full_name\":\"FelipeCarillo/agente-corretor\",\"private\":true,\"owner\":{\"login\":\"FelipeCarillo\",\"id\":63021830,\"node_id\":\"MDQ6VXNlcjYzMDIxODMw\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/63021830?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/FelipeCarillo\",\"html_url\":\"https://github.com/FelipeCarillo\",\"followers_url\":\"https://api.github.com/users/FelipeCarillo/followers\",\"following_url\":\"https://api.github.com/users/FelipeCarillo/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/FelipeCarillo/subscriptions\",\"organizations_url\":\"https://api.github.com/users/FelipeCarillo/orgs\",\"repos_url\":\"https://api.github.com/users/FelipeCarillo/repos\",\"events_url\":\"https://api.github.com/users/FelipeCarillo/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/FelipeCarillo/received_events\",\"type\":\"User\",\"user_view_type\":\"public\",\"site_admin\":false},\"html_url\":\"https://github.com/FelipeCarillo/agente-corretor\",\"description\":null,\"fork\":false,\"url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor\",\"forks_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/forks\",\"keys_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/keys{/key_id}\",\"collaborators_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/collaborators{/collaborator}\",\"teams_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/teams\",\"hooks_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/hooks\",\"issue_events_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/events{/number}\",\"events_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/events\",\"assignees_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/assignees{/user}\",\"branches_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/branches{/branch}\",\"tags_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/tags\",\"blobs_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/blobs{/sha}\",\"git_tags_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/tags{/sha}\",\"git_refs_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/refs{/sha}\",\"trees_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/trees{/sha}\",\"statuses_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/{sha}\",\"languages_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/languages\",\"stargazers_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/stargazers\",\"contributors_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/contributors\",\"subscribers_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscribers\",\"subscription_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscription\",\"commits_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/commits{/sha}\",\"git_commits_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/commits{/sha}\",\"comments_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/comments{/number}\",\"issue_comment_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/comments{/number}\",\"contents_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/contents/{+path}\",\"compare_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/compare/{base}...{head}\",\"merges_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/merges\",\"archive_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/{archive_format}{/ref}\",\"downloads_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/downloads\",\"issues_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues{/number}\",\"pulls_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls{/number}\",\"milestones_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/milestones{/number}\",\"notifications_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/notifications{?since,all,participating}\",\"labels_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/labels{/name}\",\"releases_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/releases{/id}\",\"deployments_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/deployments\",\"created_at\":\"2025-03-23T05:00:35Z\",\"updated_at\":\"2025-03-23T05:00:39Z\",\"pushed_at\":\"2025-06-13T04:40:57Z\",\"git_url\":\"git://github.com/FelipeCarillo/agente-corretor.git\",\"ssh_url\":\"git@github.com:FelipeCarillo/agente-corretor.git\",\"clone_url\":\"https://github.com/FelipeCarillo/agente-corretor.git\",\"svn_url\":\"https://github.com/FelipeCarillo/agente-corretor\",\"homepage\":null,\"size\":0,\"stargazers_count\":0,\"watchers_count\":0,\"language\":null,\"has_issues\":true,\"has_projects\":true,\"has_downloads\":true,\"has_wiki\":true,\"has_pages\":false,\"has_discussions\":false,\"forks_count\":0,\"mirror_url\":null,\"archived\":false,\"disabled\":false,\"open_issues_count\":1,\"license\":null,\"allow_forking\":true,\"is_template\":false,\"web_commit_signoff_required\":false,\"topics\":[],\"visibility\":\"private\",\"forks\":0,\"open_issues\":1,\"watchers\":0,\"default_branch\":\"main\",\"allow_squash_merge\":true,\"allow_merge_commit\":true,\"allow_rebase_merge\":true,\"allow_auto_merge\":false,\"delete_branch_on_merge\":false,\"allow_update_branch\":false,\"use_squash_pr_title_as_default\":false,\"squash_merge_commit_message\":\"COMMIT_MESSAGES\",\"squash_merge_commit_title\":\"COMMIT_OR_PR_TITLE\",\"merge_commit_message\":\"PR_TITLE\",\"merge_commit_title\":\"MERGE_MESSAGE\"}},\"base\":{\"label\":\"FelipeCarillo:main\",\"ref\":\"main\",\"sha\":\"d3e70f098e40b6cdb9d0a2bf6e42cd6b618770d8\",\"user\":{\"login\":\"FelipeCarillo\",\"id\":63021830,\"node_id\":\"MDQ6VXNlcjYzMDIxODMw\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/63021830?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/FelipeCarillo\",\"html_url\":\"https://github.com/FelipeCarillo\",\"followers_url\":\"https://api.github.com/users/FelipeCarillo/followers\",\"following_url\":\"https://api.github.com/users/FelipeCarillo/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/FelipeCarillo/subscriptions\",\"organizations_url\":\"https://api.github.com/users/FelipeCarillo/orgs\",\"repos_url\":\"https://api.github.com/users/FelipeCarillo/repos\",\"events_url\":\"https://api.github.com/users/FelipeCarillo/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/FelipeCarillo/received_events\",\"type\":\"User\",\"user_view_type\":\"public\",\"site_admin\":false},\"repo\":{\"id\":953326888,\"node_id\":\"R_kgDOONKdKA\",\"name\":\"agente-corretor\",\"full_name\":\"FelipeCarillo/agente-corretor\",\"private\":true,\"owner\":{\"login\":\"FelipeCarillo\",\"id\":63021830,\"node_id\":\"MDQ6VXNlcjYzMDIxODMw\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/63021830?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/FelipeCarillo\",\"html_url\":\"https://github.com/FelipeCarillo\",\"followers_url\":\"https://api.github.com/users/FelipeCarillo/followers\",\"following_url\":\"https://api.github.com/users/FelipeCarillo/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/FelipeCarillo/subscriptions\",\"organizations_url\":\"https://api.github.com/users/FelipeCarillo/orgs\",\"repos_url\":\"https://api.github.com/users/FelipeCarillo/repos\",\"events_url\":\"https://api.github.com/users/FelipeCarillo/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/FelipeCarillo/received_events\",\"type\":\"User\",\"user_view_type\":\"public\",\"site_admin\":false},\"html_url\":\"https://github.com/FelipeCarillo/agente-corretor\",\"description\":null,\"fork\":false,\"url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor\",\"forks_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/forks\",\"keys_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/keys{/key_id}\",\"collaborators_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/collaborators{/collaborator}\",\"teams_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/teams\",\"hooks_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/hooks\",\"issue_events_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/events{/number}\",\"events_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/events\",\"assignees_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/assignees{/user}\",\"branches_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/branches{/branch}\",\"tags_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/tags\",\"blobs_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/blobs{/sha}\",\"git_tags_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/tags{/sha}\",\"git_refs_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/refs{/sha}\",\"trees_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/trees{/sha}\",\"statuses_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/{sha}\",\"languages_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/languages\",\"stargazers_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/stargazers\",\"contributors_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/contributors\",\"subscribers_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscribers\",\"subscription_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscription\",\"commits_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/commits{/sha}\",\"git_commits_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/commits{/sha}\",\"comments_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/comments{/number}\",\"issue_comment_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/comments{/number}\",\"contents_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/contents/{+path}\",\"compare_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/compare/{base}...{head}\",\"merges_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/merges\",\"archive_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/{archive_format}{/ref}\",\"downloads_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/downloads\",\"issues_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues{/number}\",\"pulls_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls{/number}\",\"milestones_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/milestones{/number}\",\"notifications_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/notifications{?since,all,participating}\",\"labels_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/labels{/name}\",\"releases_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/releases{/id}\",\"deployments_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/deployments\",\"created_at\":\"2025-03-23T05:00:35Z\",\"updated_at\":\"2025-03-23T05:00:39Z\",\"pushed_at\":\"2025-06-13T04:40:57Z\",\"git_url\":\"git://github.com/FelipeCarillo/agente-corretor.git\",\"ssh_url\":\"git@github.com:FelipeCarillo/agente-corretor.git\",\"clone_url\":\"https://github.com/FelipeCarillo/agente-corretor.git\",\"svn_url\":\"https://github.com/FelipeCarillo/agente-corretor\",\"homepage\":null,\"size\":0,\"stargazers_count\":0,\"watchers_count\":0,\"language\":null,\"has_issues\":true,\"has_projects\":true,\"has_downloads\":true,\"has_wiki\":true,\"has_pages\":false,\"has_discussions\":false,\"forks_count\":0,\"mirror_url\":null,\"archived\":false,\"disabled\":false,\"open_issues_count\":1,\"license\":null,\"allow_forking\":true,\"is_template\":false,\"web_commit_signoff_required\":false,\"topics\":[],\"visibility\":\"private\",\"forks\":0,\"open_issues\":1,\"watchers\":0,\"default_branch\":\"main\",\"allow_squash_merge\":true,\"allow_merge_commit\":true,\"allow_rebase_merge\":true,\"allow_auto_merge\":false,\"delete_branch_on_merge\":false,\"allow_update_branch\":false,\"use_squash_pr_title_as_default\":false,\"squash_merge_commit_message\":\"COMMIT_MESSAGES\",\"squash_merge_commit_title\":\"COMMIT_OR_PR_TITLE\",\"merge_commit_message\":\"PR_TITLE\",\"merge_commit_title\":\"MERGE_MESSAGE\"}},\"_links\":{\"self\":{\"href\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1\"},\"html\":{\"href\":\"https://github.com/FelipeCarillo/agente-corretor/pull/1\"},\"issue\":{\"href\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/1\"},\"comments\":{\"href\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/1/comments\"},\"review_comments\":{\"href\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1/comments\"},\"review_comment\":{\"href\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/comments{/number}\"},\"commits\":{\"href\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls/1/commits\"},\"statuses\":{\"href\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/100ba89359e5ca61f16c12ec49bf0dd3be77f3f6\"}},\"author_association\":\"OWNER\",\"auto_merge\":null,\"active_lock_reason\":null,\"merged\":false,\"mergeable\":null,\"rebaseable\":null,\"mergeable_state\":\"unknown\",\"merged_by\":null,\"comments\":0,\"review_comments\":0,\"maintainer_can_modify\":false,\"commits\":1,\"additions\":3,\"deletions\":1,\"changed_files\":1},\"repository\":{\"id\":953326888,\"node_id\":\"R_kgDOONKdKA\",\"name\":\"agente-corretor\",\"full_name\":\"FelipeCarillo/agente-corretor\",\"private\":true,\"owner\":{\"login\":\"FelipeCarillo\",\"id\":63021830,\"node_id\":\"MDQ6VXNlcjYzMDIxODMw\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/63021830?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/FelipeCarillo\",\"html_url\":\"https://github.com/FelipeCarillo\",\"followers_url\":\"https://api.github.com/users/FelipeCarillo/followers\",\"following_url\":\"https://api.github.com/users/FelipeCarillo/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/FelipeCarillo/subscriptions\",\"organizations_url\":\"https://api.github.com/users/FelipeCarillo/orgs\",\"repos_url\":\"https://api.github.com/users/FelipeCarillo/repos\",\"events_url\":\"https://api.github.com/users/FelipeCarillo/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/FelipeCarillo/received_events\",\"type\":\"User\",\"user_view_type\":\"public\",\"site_admin\":false},\"html_url\":\"https://github.com/FelipeCarillo/agente-corretor\",\"description\":null,\"fork\":false,\"url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor\",\"forks_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/forks\",\"keys_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/keys{/key_id}\",\"collaborators_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/collaborators{/collaborator}\",\"teams_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/teams\",\"hooks_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/hooks\",\"issue_events_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/events{/number}\",\"events_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/events\",\"assignees_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/assignees{/user}\",\"branches_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/branches{/branch}\",\"tags_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/tags\",\"blobs_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/blobs{/sha}\",\"git_tags_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/tags{/sha}\",\"git_refs_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/refs{/sha}\",\"trees_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/trees{/sha}\",\"statuses_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/statuses/{sha}\",\"languages_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/languages\",\"stargazers_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/stargazers\",\"contributors_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/contributors\",\"subscribers_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscribers\",\"subscription_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/subscription\",\"commits_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/commits{/sha}\",\"git_commits_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/git/commits{/sha}\",\"comments_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/comments{/number}\",\"issue_comment_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues/comments{/number}\",\"contents_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/contents/{+path}\",\"compare_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/compare/{base}...{head}\",\"merges_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/merges\",\"archive_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/{archive_format}{/ref}\",\"downloads_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/downloads\",\"issues_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/issues{/number}\",\"pulls_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/pulls{/number}\",\"milestones_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/milestones{/number}\",\"notifications_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/notifications{?since,all,participating}\",\"labels_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/labels{/name}\",\"releases_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/releases{/id}\",\"deployments_url\":\"https://api.github.com/repos/FelipeCarillo/agente-corretor/deployments\",\"created_at\":\"2025-03-23T05:00:35Z\",\"updated_at\":\"2025-03-23T05:00:39Z\",\"pushed_at\":\"2025-06-13T04:40:57Z\",\"git_url\":\"git://github.com/FelipeCarillo/agente-corretor.git\",\"ssh_url\":\"git@github.com:FelipeCarillo/agente-corretor.git\",\"clone_url\":\"https://github.com/FelipeCarillo/agente-corretor.git\",\"svn_url\":\"https://github.com/FelipeCarillo/agente-corretor\",\"homepage\":null,\"size\":0,\"stargazers_count\":0,\"watchers_count\":0,\"language\":null,\"has_issues\":true,\"has_projects\":true,\"has_downloads\":true,\"has_wiki\":true,\"has_pages\":false,\"has_discussions\":false,\"forks_count\":0,\"mirror_url\":null,\"archived\":false,\"disabled\":false,\"open_issues_count\":1,\"license\":null,\"allow_forking\":true,\"is_template\":false,\"web_commit_signoff_required\":false,\"topics\":[],\"visibility\":\"private\",\"forks\":0,\"open_issues\":1,\"watchers\":0,\"default_branch\":\"main\"},\"sender\":{\"login\":\"FelipeCarillo\",\"id\":63021830,\"node_id\":\"MDQ6VXNlcjYzMDIxODMw\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/63021830?v=4\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/FelipeCarillo\",\"html_url\":\"https://github.com/FelipeCarillo\",\"followers_url\":\"https://api.github.com/users/FelipeCarillo/followers\",\"following_url\":\"https://api.github.com/users/FelipeCarillo/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/FelipeCarillo/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/FelipeCarillo/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/FelipeCarillo/subscriptions\",\"organizations_url\":\"https://api.github.com/users/FelipeCarillo/orgs\",\"repos_url\":\"https://api.github.com/users/FelipeCarillo/repos\",\"events_url\":\"https://api.github.com/users/FelipeCarillo/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/FelipeCarillo/received_events\",\"type\":\"User\",\"user_view_type\":\"public\",\"site_admin\":false}}",
        "isBase64Encoded": False
    }

    lambda_handler(event, None)
