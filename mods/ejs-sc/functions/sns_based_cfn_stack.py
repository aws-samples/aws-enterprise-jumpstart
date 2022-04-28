import json
import urllib3
from botocore.config import Config
import botocore
import boto3
import enum
import traceback
import time


CREATE_SUCCEEDED = "CREATE_COMPLETE"
CREATE_FAILED = ["CREATE_FAILED", "ROLLBACK_COMPLETE", "ROLLBACK_FAILED"]
DELETE_SUCCEEDED = "DELETE_COMPLETE"
DELETE_FAILED = ["DELETE_FAILED", "ROLLBACK_COMPLETE", "ROLLBACK_FAILED"]
UPDATE_SUCCEEDED = "UPDATE_COMPLETE"
UPDATE_FAILED = ["UPDATE_FAILED", "ROLLBACK_COMPLETE", "ROLLBACK_FAILED", "UPDATE_ROLLBACK_COMPLETE"]


boto3_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)
cfn = boto3.client("cloudformation", config=boto3_config)
http = urllib3.PoolManager()

class Status(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


def lambda_handler(event, context):
    try:
        msg = json.loads(event["Records"][0]["Sns"]["Message"])
        print(json.dumps(msg))
        properties = msg['ResourceProperties']
        stack_name = properties["StackName"]
        tmpl = properties["Template"]
        parameters_list = properties["Parameters"]
        if msg["RequestType"] == "Create":
            create_handler(stack_name, tmpl, parameters_list, msg, context)
            return
        if msg["RequestType"] == "Update":
            update_handler(stack_name, tmpl, parameters_list, msg, context)
            return
        if msg["RequestType"] == "Delete":
            delete_handler(stack_name, tmpl, parameters_list, msg, context)
            return
        
        raise Exception("wrong request type")
    except Exception as e:
        print(traceback.format_exc())
        send(msg, context, Status.FAILED, {}, reason=str(e))


def create_handler(stack_name, tmpl, parameters, msg, ctx):
    stack = cfn.create_stack(
        StackName=stack_name,
        TemplateBody=tmpl,
        Parameters=parameters
    )['StackId']
    if wait_for_complete(stack, CREATE_SUCCEEDED, CREATE_FAILED, "Create"):
        send(msg, ctx, Status.SUCCESS, {}, physical_resource_id=stack)
    else:
        raise Exception("create failed")


def update_handler(stack_name, tmpl, parameters, msg, ctx):
    stack = cfn.update_stack(
        StackName=stack_name,
        TemplateBody=tmpl,
        Parameters=parameters
    )['StackId']
    if wait_for_complete(stack, UPDATE_SUCCEEDED, UPDATE_FAILED, "Update"):
        send(msg, ctx, Status.SUCCESS, {}, physical_resource_id=stack)
    else:
        raise Exception("update failed")


def delete_handler(stack_name, tmpl, parameters, msg, ctx):
    cfn.delete_stack(
        StackName=stack_name
    )
    if wait_for_complete(stack_name, DELETE_SUCCEEDED, DELETE_FAILED, "Delete"):
        send(msg, ctx, Status.SUCCESS, {})
    else:
        raise Exception("delete failed")


def wait_for_complete(stack_name, success_status, failed_status, request_type):
    while True:
        try:
            descr = cfn.describe_stacks(StackName=stack_name)['Stacks'][0]
        except botocore.exceptions.ClientError as e:
            if request_type == 'Delete' and "does not exist" in str(e):
                return True
            else:
                return False
        
        status = descr['StackStatus']
        if status == success_status:
            return True
        if status in failed_status:
            return False
            
        time.sleep(5)


def send(event, context, response_status, response_data, physical_resource_id=None, no_echo=False, reason=None):
    response_url = event['ResponseURL']
    print(response_url)

    response_body = {
        'Status': response_status.name,
        'Reason': reason or "See the details in CloudWatch Log Stream: {}".format(context.log_stream_name),
        'PhysicalResourceId': physical_resource_id or context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': no_echo,
        'Data': response_data
    }

    json_response_body = json.dumps(response_body)

    print("Response body:")
    print(json_response_body)

    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }

    try:
        response = http.request('PUT', response_url, headers=headers, body=json_response_body)
        print("Status code:", response.status)

    except Exception as e:
        print("send(..) failed executing http.request(..):", e)
