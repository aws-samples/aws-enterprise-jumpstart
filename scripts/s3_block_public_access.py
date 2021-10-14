import json
import logging

import boto3
from botocore.config import Config
import os

ROLE_NAME = os.getenv('ROLE_NAME')

log_level = logging.INFO if os.getenv('LOG_LEVEL') is None else int(os.getenv('LOG_LEVEL'))
logger = logging.getLogger()
logger.setLevel(log_level)


def lambda_handler(event, context):
    logging.info(f"log_level: {log_level}")

    logging.info(json.dumps(event))
    status = event['detail']['serviceEventDetails']['createAccountStatus']
    account_id = status['accountId']
    boto3_config = Config(
        retries={
            'max_attempts': 10,
            'mode': 'standard'
        }
    )
    sts_client = boto3.client('sts', config=boto3_config)
    role_object = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/{ROLE_NAME}",
        RoleSessionName="SetupBlockPublicAccess"
    )
    credentials = role_object['Credentials']
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )
  
    s3_client = boto3.client('s3control', config=boto3_config)
    response = s3_client.put_public_access_block(
        AccountId=account_id,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
            }
    )
    logging.debug(json.dumps(response))