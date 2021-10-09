import json
import logging

import boto3
from botocore.config import Config
import os


ROLE_NAME = os.getenv('ROLE_NAME')
REGIONS = os.getenv('REGIONS').split(',')

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
        RoleSessionName="DeleteDefaultVpc"
    )
    credentials = role_object['Credentials']
    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )
    for region in REGIONS:
        logging.info(region)
        ec2 = session.resource("ec2", region_name=region, config=boto3_config)
        vpcs = ec2.vpcs.all()
        for vpc in [vpc for vpc in vpcs if vpc.is_default is True]:
            for internet_gateway in vpc.internet_gateways.all():
                internet_gateway.detach_from_vpc(VpcId=vpc.vpc_id)
                internet_gateway.delete()

            for subnet in vpc.subnets.all():
                subnet.delete()

            vpc.delete()
