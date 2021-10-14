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

BLUEPRINTS_KEY = "blueprints"
artifacts_bucket_name = os.getenv("ARTIFACTS_BUCKET_NAME")
artifacts_bucket_prefix = os.getenv("ARTIFACTS_BUCKET_SC_ASSET_PREFIX")
region = os.getenv("AWS_REGION")

artifact_bucket = boto3.resource("s3").Bucket(artifacts_bucket_name)
s3_client = boto3.client("s3", config=boto3_config)
sc_client = boto3.client("servicecatalog", config=boto3_config)
ssm_client = boto3.client('ssm', config=boto3_config)


def __cleanup_versions(_name, _versions, _product_id):
    pa_list = sc_client.list_provisioning_artifacts(
        ProductId=_product_id
    )['ProvisioningArtifactDetails']
    for pa in pa_list:
        if pa['Name'] != 'DUMMY' and len(list(filter(lambda x: x['name'] == pa['Name'], _versions))) <= 0:
            sc_client.delete_provisioning_artifact(
                ProductId=_product_id,
                ProvisioningArtifactId=pa['Id']
            )


with open(f"{BLUEPRINTS_KEY}/metadata.yaml", 'r') as stream:
    blueprints = yaml.safe_load(stream)[BLUEPRINTS_KEY]
    for name, blueprint in blueprints.items():
        product_id = ssm_client.get_parameter(Name=f"/blueprints/{name}/id")['Parameter']['Value']
        print(f"#### {name} - {product_id} ####")
        __cleanup_versions(name, blueprint['versions'])
        for version in blueprint['versions']:
            print(version)
            key = "{}/{}/{}.yaml".format(artifacts_bucket_prefix, name, version['name'])
            obj = artifact_bucket.Object(key)
            try:
                obj.get()
            except s3_client.exceptions.NoSuchKey as e:
                # If version does not already exists upload template and create new provisioning artifact version
                print(f"Uploading version {key}")
                artifact_bucket.upload_file(f"{BLUEPRINTS_KEY}/{name}.yaml", key)
                obj_url = f"https://{artifacts_bucket_name}.s3.{region}.amazonaws.com/{artifacts_bucket_prefix}/{name}/{version['name']}.yaml"
                try:
                    sc_client.describe_provisioning_artifact(
                        ProductId=product_id,
                        ProvisioningArtifactName=version['name']
                    )
                    err_msg = f"Provisioning Artifact on product {name} ({product_id}) with name {version['name']} already exists"
                    print(err_msg)
                    raise Exception(err_msg)
                except sc_client.exceptions.ResourceNotFoundException as e:
                    print(f"Create new provisioning artifact version for template:")
                    print(obj_url)
                    sc_client.create_provisioning_artifact(
                        ProductId=product_id,
                        Parameters={
                            'Name': version['name'],
                            'Description': version['description'],
                            'Info': {
                                'LoadTemplateFromURL': obj_url
                            },
                            'Type': 'CLOUD_FORMATION_TEMPLATE'
                        },
                    )


            
