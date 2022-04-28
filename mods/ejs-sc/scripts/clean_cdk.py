# TODO: hacky workaround to clean the cdk generated Cfn template.
# works without when bootsrapping cdk first or using cdk deploy instead of proper codepipeline cfn action
import json
import boto3

# asset_list = json.load(open('dist/CdkStack.template.json', 'r'))['files']
# for key in asset_list:
#     asset = asset_list[key]
#     print(json.dumps(asset))
#     s3 = boto3.resource('s3')
#     bucket = s3.Bucket(asset['destinations']['current_account-current_region']['bucketName'])
#     source_file = asset['source']['path']
#     s3_key = asset['destinations']['current_account-current_region']['objectKey']
#     bucket.upload_file(Filename=f"dist/{source_file}", Key=s3_key)

tmpl = json.load(open('dist/CdkStack.template.json', 'r'))
del tmpl['Parameters']['BootstrapVersion']
del tmpl['Conditions']
del tmpl['Rules']
del tmpl['Resources']['CDKMetadata']

with open('dist/CdkStack.template.json', 'w') as f:
    print(json.dumps(tmpl))
    json.dump(tmpl, f)
