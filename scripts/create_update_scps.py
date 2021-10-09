import json
import traceback

import os
import re

import boto3
import yaml
from botocore.config import Config


SCPS_KEY = "scps"
PREFIX = os.getenv("SERVICE_NAME") if os.getenv("SERVICE_NAME") else "enterprise-jumpstart"

boto3_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)


def __get_policy_by_name(_paginator, scp_name):
    for page in _paginator.paginate(Filter='SERVICE_CONTROL_POLICY'):
        for __scp in page["Policies"]:
            if __scp["Name"] == scp_name:
                return __scp
    return None


ssm_client = boto3.client('ssm', config=boto3_config)
org_id = ssm_client.get_parameter(Name='/org/management-account/id')['Parameter']['Value']

sts_client = boto3.client('sts', config=boto3_config)
role_object = sts_client.assume_role(
    RoleArn=f"arn:aws:iam::{org_id}:role/DeploymentAccountAccessRole",
    RoleSessionName="ScpUpdateCreateAction"
)
credentials = role_object['Credentials']
session = boto3.Session(
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken'],
)
org_client = session.client("organizations", region_name='us-east-1', config=boto3_config)

with open("scps/metadata.yaml", 'r') as stream:
    scps = yaml.safe_load(stream)[SCPS_KEY]
    for name, scp in scps.items():
        try:
            _name = f"{PREFIX}-{name}"
            print(f"********* CREATE_OR_UPDATE_SCP - {_name} *********")
            print(scp)
            with open(f"scps/{name}.json", 'r') as scp_stream:
                scp_content = json.load(scp_stream)
                scp_plain = json.dumps(scp_content)
                for match in re.finditer(r'(?P<full>\{\{resolve:ssm:(?P<parameter>(/[a-zA-Z0-9-_]+)+)\}\})', scp_plain):
                    full_match = match.group('full')
                    parameter_name = match.group('parameter')
                    parameter_response = ssm_client.get_parameter(Name=parameter_name)['Parameter']
                    if parameter_response['Type'] == 'StringList':
                        parameter_value = json.dumps(parameter_response['Value'].split(',')).replace("[\"", "").replace("\"]", "")
                    else:
                        parameter_value = parameter_response['Value']
                    print(f"Parameter {parameter_name} found, value: '{parameter_value}'")
                    scp_plain = scp_plain.replace(full_match, parameter_value)

                try:
                    _scp = org_client.create_policy(
                        Content=scp_plain,
                        Description=scp['description'],
                        Name=_name,
                        Type='SERVICE_CONTROL_POLICY'
                    )['Policy']['PolicySummary']
                except org_client.exceptions.DuplicatePolicyException as e:
                    print(f"SCP with name {_name} exists, search for exists SCP.")
                    paginator = org_client.get_paginator('list_policies')
                    _scp = __get_policy_by_name(paginator, _name)
                    print(f"Updating existing SCP ({_scp['Id']}).")
                    org_client.update_policy(
                        PolicyId=_scp['Id'],
                        Content=scp_plain,
                        Description=scp['description'],
                        Name=_name
                    )

                print("ATTACH_OR_RE-ATTACH_SCP")
                try:
                    org_client.attach_policy(
                        PolicyId=_scp['Id'],
                        TargetId=scp['organizational-unit-id']
                    )
                except org_client.exceptions.DuplicatePolicyAttachmentException as e:
                    print(f"SCP {_name} ({_scp['Id']}) already attached to OU ({scp['organizational-unit-id']}).")
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())
            raise e
