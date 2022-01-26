import logging
import os
import time

import boto3
import yaml
from botocore.config import Config

log_level = logging.INFO if os.getenv('LOG_LEVEL') is None else int(os.getenv('LOG_LEVEL'))
logging.basicConfig(format='%(levelname)s:%(asctime)s - %(message)s', level=log_level)
logging.info(f"log_level: {log_level}")
boto3_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)
LAUNCH_PATH_NAME = 'Account Blueprints'
organization_unit = os.getenv('ORGANIZATIONAL_UNIT')
product_id = os.getenv('PRODUCT_ID')
provisioning_artifact_name = os.getenv('PRODUCT_VERSION_NAME')

org_client = boto3.client("organizations", config=boto3_config)
sc_client = boto3.client("servicecatalog", config=boto3_config)

if organization_unit is None or product_id is None or provisioning_artifact_name is None:
    raise Exception('Missing environment variables, make sure to set all three: ORGANIZATIONAL_UNIT, PRODUCT_ID, PRODUCT_VERSION_NAME')


def __list_accounts_for_parent(_parent):
    _paginator = org_client.get_paginator('list_accounts_for_parent')
    for page in _paginator.paginate(ParentId=_parent):
        for account in page["Accounts"]:
            yield account


def __search_provisioned_products(_product_id):
    _sc_paginator = sc_client.get_paginator('scan_provisioned_products')
    for page in _sc_paginator.paginate(AccessLevelFilter={'Key': 'Account', 'Value': 'self'}):
        for pp in page['ProvisionedProducts']:
            if pp['ProductId'] == _product_id:
                yield pp


# accounts = __list_accounts_for_parent(organization_unit)
provisioned_products = __search_provisioned_products(product_id)

for pp in provisioned_products:
    try:
        logging.info(f"Account: {pp['Name']}")
        record_detail = sc_client.describe_record(
            Id=pp['LastRecordId']
        )['RecordDetail']
        try:
            pa_detail = sc_client.describe_provisioning_artifact(
                ProductId=product_id,
                ProvisioningArtifactId=record_detail['ProvisioningArtifactId']
            )['ProvisioningArtifactDetail']
            if 'dummy' in pa_detail['Name'].lower():
                logging.info('is dummy account, skip upgrade')
                continue

        except sc_client.exceptions.ResourceNotFoundException as not_found_e:
            logging.info(f"provisioning artifact {record_detail['ProvisioningArtifactId']} not found, cannot be dummy")

        try:
            provisioning_parameters = sc_client.describe_provisioning_parameters(
                ProductId=product_id,
                ProvisioningArtifactId=pp['ProvisioningArtifactId'],
                PathName=LAUNCH_PATH_NAME
            )['ProvisioningArtifactParameters']
        except sc_client.exceptions.ResourceNotFoundException as not_found_e:
            provisioning_parameters = sc_client.describe_provisioning_parameters(
                ProductId=product_id,
                ProvisioningArtifactName=provisioning_artifact_name,
                PathName=LAUNCH_PATH_NAME
            )['ProvisioningArtifactParameters']

        logging.debug(provisioning_parameters)
        update_parameters = list(map(lambda p: {'Key': p['ParameterKey'], 'Value': '', 'UsePreviousValue': True}, provisioning_parameters))
        logging.debug(update_parameters)
        record_detail = sc_client.update_provisioned_product(
            ProductId=product_id,
            ProvisionedProductId=pp['Id'],
            PathName=LAUNCH_PATH_NAME,
            ProvisioningParameters=update_parameters,
            ProvisioningArtifactName=provisioning_artifact_name
        )['RecordDetail']
        while True:
            record_response = sc_client.describe_record(Id=record_detail["RecordId"])
            status = record_response['RecordDetail']['Status']
            if status == 'SUCCEEDED':
                break
            if status == 'FAILED':
                logging.warning(f"FAILED-----xxxx-----{pp['Name']}-----xxxx-----FAILED")
                break
            logging.debug(f"Waiting for Account {pp['Name']} finished updating")
            time.sleep(5)
    except Exception as e:
        logging.warning(str(e))
        logging.warning(f"FAILED-----xxxx-----{pp['Name']}-----xxxx-----FAILED")

