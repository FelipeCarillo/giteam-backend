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


def verify_github_signature(payload_body, secret_token, signature_header):
    """Verifica se a assinatura do GitHub é válida"""
    if not signature_header:
        return False

    if signature_header.startswith('sha256='):
        signature_header = signature_header[7:]

    expected_signature = hmac.new(
        secret_token.encode('utf-8'),
        payload_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)


def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        raw_body = event.get('body', '')
        body = json.loads(raw_body)
        headers = event.get('headers', {})

        github_signature = headers.get('X-Hub-Signature-256') or headers.get('x-hub-signature-256')

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

        if not verify_github_signature(raw_body, repository_webhook.secret, github_signature):
            logger.error("Invalid GitHub signature")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'error',
                    'message': 'Invalid signature'
                })
            }

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