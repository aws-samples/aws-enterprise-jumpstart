import boto3
import json
import urllib3
import uuid
import enum
from botocore.config import Config
import os


http = urllib3.PoolManager()
boto3_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)


class Status(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


AWS_REGION = os.getenv('AWS_REGION')


def handle_event(event, context):
    try:
        print(json.dumps(event))
        msg = json.loads(event['Records'][0]['Sns']['Message'])
        print(json.dumps(msg))
        request_type = msg['RequestType']
        properties = msg['ResourceProperties']

        tgw_attachment_id = properties['TgwAttachmentId']
        vpc_identifier = properties['Identifier']
        r53_private_hosted_zone = properties['R53PrivateHostedZoneId']
        vpc_id = properties['VpcId']
        route_table_id = properties['RouteTableId']
        ssm_client = boto3.client('ssm', config=boto3_config)
        tgw_hub_route_table = ssm_client.get_parameter(Name="/networking/{}/route-table/hub".format(AWS_REGION))['Parameter']['Value']
        ec2_client = boto3.client('ec2', config=boto3_config)
        if request_type == 'Create':
            ec2_client.associate_transit_gateway_route_table(
                TransitGatewayRouteTableId=route_table_id,
                TransitGatewayAttachmentId=tgw_attachment_id
            )
            ec2_client.enable_transit_gateway_route_table_propagation(
                TransitGatewayRouteTableId=tgw_hub_route_table,
                TransitGatewayAttachmentId=tgw_attachment_id
            )
            send(msg, context, Status.SUCCESS, {}, physical_resource_id=str(uuid.uuid4()))
        if request_type == 'Delete':
            ec2_client.disassociate_transit_gateway_route_table(
                TransitGatewayRouteTableId=route_table_id,
                TransitGatewayAttachmentId=tgw_attachment_id
            )
            ec2_client.disable_transit_gateway_route_table_propagation(
                TransitGatewayRouteTableId=tgw_hub_route_table,
                TransitGatewayAttachmentId=tgw_attachment_id
            )
            send(msg, context, Status.SUCCESS, {}, physical_resource_id=str(uuid.uuid4()))
        if request_type == 'Update':
            send(msg, context, Status.FAILED, {}, reason='Update on this resource is not supported')
    except Exception as e:
        print(str(e))
        send(msg, context, Status.FAILED, {}, reason=str(e))
        raise(e)


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
