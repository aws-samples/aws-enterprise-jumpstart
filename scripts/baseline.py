import json

import boto3
import os

import botocore
from botocore.config import Config

boto3_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)


type_arn = os.getenv('ORG_ACCOUNT_RESOURCE_TYPE_ARN')
cfn_role_arn = os.getenv('JUMPSTART_CFN_ROLE_ARN')
kms_key_arn = os.getenv('ARTIFACTS_KMS_KEY_ARN')


def main():
    ssm_client = boto3.client('ssm')
    org_account_id = ssm_client.get_parameter(Name='/org/management-account/id')['Parameter']['Value']
    org_prefix = ssm_client.get_parameter(Name='/org/prefix')['Parameter']['Value']

    print('configure cross-account functionality for org account cfn resource')
    org_account_role = f"arn:aws:iam::{org_account_id}:role/DeploymentAccountAccessRole"
    cfn_client = boto3.client('cloudformation')
    config = {
        'RoleArn': org_account_role
    }
    cfn_client.set_type_configuration(
        TypeArn=type_arn,
        Configuration=json.dumps(config),
        ConfigurationAlias='standard',
        Type='RESOURCE'
    )

    print("deploy artifact store in us-east-1")
    parameters = [
                        {
                            'ParameterKey': 'ManagedResourcePrefix',
                            'ParameterValue': org_prefix,
                        },
                        {
                            'ParameterKey': 'OrganizationManagementAccountId',
                            'ParameterValue': org_account_id,
                        },
                        {
                            'ParameterKey': 'KmsKeyArn',
                            'ParameterValue': kms_key_arn,
                        }
                    ]
    cfn_client_us = boto3.client('cloudformation', region_name='us-east-1', config=boto3_config)
    with open("deployment/artifact-store.yaml", 'r') as stream:
        tmpl = stream.read()
        try:
            stack_response = cfn_client_us.create_stack(
                StackName=f"{org_prefix}-artifact-store",
                RoleARN=cfn_role_arn,
                Parameters=parameters,
                TemplateBody=tmpl,
                OnFailure='DELETE'
            )
            waiter = cfn_client_us.get_waiter('stack_create_complete')
            waiter.wait(
                StackName=stack_response['StackId'],
                WaiterConfig={
                    'Delay': 10,
                    'MaxAttempts': 120
                }
            )
        except cfn_client_us.exceptions.AlreadyExistsException as e:
            print('stack exists, try to update')
            try:
                stack_response = cfn_client_us.update_stack(
                    StackName=f"{org_prefix}-artifact-store",
                    RoleARN=cfn_role_arn,
                    Parameters=parameters,
                    TemplateBody=tmpl
                )
                waiter = cfn_client_us.get_waiter('stack_update_complete')
                waiter.wait(
                    StackName=stack_response['StackId'],
                    WaiterConfig={
                        'Delay': 10,
                        'MaxAttempts': 120
                    }
                )
            except botocore.exceptions.ClientError as e:
                if "No updates are to be performed" in str(e):
                    print("No updates are to be performed")
                else:
                    raise e


if __name__ == "__main__":
    main()
