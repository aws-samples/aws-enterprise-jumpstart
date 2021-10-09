import json
import traceback

import os
import re

import boto3
import yaml
from botocore.config import Config


boto3_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)


ssm_client = boto3.client('ssm', config=boto3_config)
org_prefix = ssm_client.get_parameter(Name='/org/prefix')['Parameter']['Value']
audit_account_id = ssm_client.get_parameter(Name='/org/security-audit-account/id')['Parameter']['Value']
log_account_id = ssm_client.get_parameter(Name='/org/log-archive-account/id')['Parameter']['Value']
role_name = ssm_client.get_parameter(Name='/org/deployment-account-access-role/name')['Parameter']['Value']

assume_role_policy = {
                        'Version': '2012-10-17',
                        'Statement': [
                            {
                                'Effect': 'Allow',
                                'Principal': {
                                    'Service': 'cloudformation.amazonaws.com'
                                },
                                'Action': 'sts:AssumeRole'
                            }
                        ]
                    }


def create_cfn_admin_role(_iam_client):
    try:
        _iam_client.create_role(
            RoleName='CfnAdmin',
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description='Enterprise Jumpstart Cloudformation role'
        )
        _iam_client.attach_role_policy(
            RoleName='CfnAdmin',
            PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
        )
    except _iam_client.exceptions.EntityAlreadyExistsException:
        print("Role already exists in account - skipping")


sts_client = boto3.client('sts', config=boto3_config)


print("baseline audit account")
role_object = sts_client.assume_role(
    RoleArn=f"arn:aws:iam::{audit_account_id}:role/{role_name}",
    RoleSessionName="SecurityBaselineAction"
)
credentials = role_object['Credentials']
session = boto3.Session(
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken'],
)
iam_client = session.client("iam", region_name='us-east-1', config=boto3_config)
create_cfn_admin_role(iam_client)


print("baseline log archive account")
role_object = sts_client.assume_role(
    RoleArn=f"arn:aws:iam::{log_account_id}:role/{role_name}",
    RoleSessionName="SecurityBaselineAction"
)
credentials = role_object['Credentials']
session = boto3.Session(
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken'],
)
iam_client = session.client("iam", region_name='us-east-1', config=boto3_config)
create_cfn_admin_role(iam_client)
