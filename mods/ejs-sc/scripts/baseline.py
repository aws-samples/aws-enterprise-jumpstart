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
network_prefix = os.getenv('SERVICE_NAME')
regions = os.getenv('REGIONS').split(',')


def main():
    print(f"deploy artifact store in regions: {regions}")
    parameters = [
        {
            'ParameterKey': 'ManagedResourcePrefix',
            'ParameterValue': network_prefix,
        },
        {
            'ParameterKey': 'KmsKeyArn',
            'ParameterValue': kms_key_arn,
        }
    ]
    for region in regions:
        if region == '':
            continue
        cfn_client = boto3.client('cloudformation', region_name=region, config=boto3_config)
        with open("deployment/artifact-store.yaml", 'r') as stream:
            tmpl = stream.read()
            try:
                stack_response = cfn_client.create_stack(
                    StackName=f"{network_prefix}-artifact-store",
                    RoleARN=cfn_role_arn,
                    Parameters=parameters,
                    TemplateBody=tmpl,
                    OnFailure='DELETE'
                )
                waiter = cfn_client.get_waiter('stack_create_complete')
                waiter.wait(
                    StackName=stack_response['StackId'],
                    WaiterConfig={
                        'Delay': 10,
                        'MaxAttempts': 120
                    }
                )
            except cfn_client.exceptions.AlreadyExistsException as e:
                print('stack exists, try to update')
                try:
                    stack_response = cfn_client.update_stack(
                        StackName=f"{network_prefix}-artifact-store",
                        RoleARN=cfn_role_arn,
                        Parameters=parameters,
                        TemplateBody=tmpl
                    )
                    waiter = cfn_client.get_waiter('stack_update_complete')
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
