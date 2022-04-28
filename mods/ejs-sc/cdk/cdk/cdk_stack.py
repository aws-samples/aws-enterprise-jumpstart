import json

from aws_cdk import (
    Stack,
    aws_secretsmanager as secrets,
    aws_servicecatalog as sc,
    aws_ssm as ssm,
    aws_iam as iam, CfnParameter, CfnDeletionPolicy
)
from constructs import Construct
import os
import boto3
import yaml
from botocore.config import Config

boto3_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)

PRODUCTS_KEY = "products"
# PROVIDER_NAME = "Product Compute Team"
artifacts_bucket_name = os.getenv("ARTIFACTS_BUCKET_NAME")
artifacts_bucket_prefix = os.getenv("ARTIFACTS_BUCKET_SC_ASSET_PREFIX")
region = os.getenv("AWS_REGION")

artifact_bucket = boto3.resource("s3").Bucket(artifacts_bucket_name)
s3_client = boto3.client("s3", config=boto3_config)
sc_client = boto3.client("servicecatalog", config=boto3_config)
ssm_client = boto3.client('ssm', config=boto3_config)

class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        portfolio = sc.CfnPortfolio(
            self,
            "OrgScPortfolioSSPM",
            display_name="Org SC Offering ",
            provider_name="Landing Zone Team",
            description="Service Catalog Offering Permissions"
        )

        # launch_role = iam.CfnRole(
        #     self,
        #     "ServiceCatalogLaunchRole",
        #     role_name=f"{os.getenv('SERVICE_NAME')}-sc-launch",
        #     assume_role_policy_document={
        #         "Version": "2012-10-17",
        #         "Statement": [
        #             {
        #                 "Effect": "Allow",
        #                 "Principal": {
        #                     "Service": "servicecatalog.amazonaws.com"
        #                 },
        #                 "Action": [
        #                     "sts:AssumeRole"
        #                 ]
        #             }
        #         ]
        #     },
        #     managed_policy_arns=[
        #         "arn:aws:iam::aws:policy/AdministratorAccess"
        #     ]
        # )

        with open("../metadata.yaml", 'r') as stream:
            products = yaml.safe_load(stream)[PRODUCTS_KEY]
            for name, product in products.items():
                versions = []
                for version in product['versions']:
                    print(version)
                    key = "{}/{}/{}.yaml".format(artifacts_bucket_prefix, name, version['name'])
                    obj = artifact_bucket.Object(key)
                    obj_url = f"https://{artifacts_bucket_name}.s3.{region}.amazonaws.com/{artifacts_bucket_prefix}/{name}/{version['name']}.yaml"
                    try:
                        obj.get()
                    except s3_client.exceptions.NoSuchKey as e:
                        # If version does not already exists upload template and create new provisioning artifact version
                        print(f"Uploading version {key}")
                        artifact_bucket.upload_file(f"../{PRODUCTS_KEY}/{name}.yaml", key)

                    versions.append({
                        'name': version['name'],
                        'description': version['description'],
                        'info': {
                            'LoadTemplateFromURL': obj_url
                        }
                    })

                product = sc.CfnCloudFormationProduct(
                    self,
                    name.capitalize(),
                    name=name,
                    owner="Landing Zone Team",
                    description=f"Product: {name.capitalize()}",
                    provisioning_artifact_parameters=versions
                )
                product_association = sc.CfnPortfolioProductAssociation(
                    self,
                    f"{name.capitalize()}PortfolioAssociation",
                    portfolio_id=portfolio.ref,
                    product_id=product.ref
                )
                product_launch_constraint = sc.CfnLaunchRoleConstraint(
                    self,
                    f"{name.capitalize()}LaunchConstraint",
                    portfolio_id=portfolio.ref,
                    product_id=product.ref,
                    description=f"{name.capitalize()} Account Launch Constraint",
                    local_role_name=f"{os.getenv('SERVICE_NAME')}-sc-launch"
                )
                product_launch_constraint.add_depends_on(product_association)
                ssm.CfnParameter(
                    self,
                    f"{name.capitalize()}Parameter",
                    name=f"/product/{name}/id",
                    type="String",
                    value=product.ref,
                )
