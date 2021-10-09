import hashlib
import os

import boto3
from cfn_tools import load_yaml, dump_yaml

BLOCKSIZE = 65536
TEMPLATES_PREFIX = ""
RESOURCES_KEY = "Resources"
bucket_name = os.getenv("ARTIFACT_BUCKET_NAME")
bucket_prefix = os.getenv("ARTIFACTS_BUCKET_PREFIX")
print(f">- uploading to bucket {bucket_name}")

artifact_bucket = boto3.resource("s3").Bucket(bucket_name)

with open("templates/baseline-stacksets.yaml", "r") as stream:
    template = load_yaml(stream)
resources = template[RESOURCES_KEY]

stackset_resources = {name: value for name, value in resources.items() if value["Type"] == "AWS::CloudFormation::StackSet"}
for name, value in stackset_resources.items():
    url = value["Properties"]["TemplateURL"]

    hasher = hashlib.sha256()
    local_template_path = "{}{}".format(TEMPLATES_PREFIX, url)
    with open(local_template_path, "rb") as template_file:
        buf = template_file.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = template_file.read(BLOCKSIZE)
    s3_key = hasher.hexdigest()
    template[RESOURCES_KEY][name]["Properties"]["TemplateURL"] = "https://{}.s3.amazonaws.com/{}/{}".format(
        bucket_name, bucket_prefix, s3_key
    )
    artifact_bucket.upload_file(local_template_path, "{}/{}".format(bucket_prefix, s3_key))

with open("build/pre-packaged.yaml", "w") as target_file:
    target_file.write(dump_yaml(template))
