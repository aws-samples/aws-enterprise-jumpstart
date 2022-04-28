import boto3
import re
import os
import logging
import json


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# TODO: parameterize tag to evaluate
TAG_KEY = ""

# TODO: example aws-accout-admin
CONST_PREFIX=''
g_account_pattern = '^'+CONST_PREFIX+'-(\w*)-(\w*)'

PSET_NAME_MAPPING_DICT= { 
    'r':'ReadOnlyAccess',
    'a':'Administrator',
    'p':'PowerUserAccess',
}

def list_sso_instances():
    sso_admin_client = boto3.client('sso-admin')

    sso_instance_list = []
    response = sso_admin_client.list_instances()
    for sso_instance in response['Instances']:
        # add only relevant keys to return
        sso_instance_list.append({'instanceArn': sso_instance["InstanceArn"],
                                'identityStore': sso_instance["IdentityStoreId"]
                                 })
    return sso_instance_list  
    
def list_permission_sets(ssoInstanceArn):
    sso_admin_client = boto3.client('sso-admin')
    perm_set_dict = {}
    response = sso_admin_client.list_permission_sets(InstanceArn=ssoInstanceArn)
    results = response["PermissionSets"]
    while "NextToken" in response:
        response = sso_admin_client.list_permission_sets(InstanceArn=ssoInstanceArn, 
                                                         NextToken=response["NextToken"])
        results.extend(response["PermissionSets"])

    for permission_set in results:
        perm_description = sso_admin_client.describe_permission_set(InstanceArn=ssoInstanceArn,
                                                                    PermissionSetArn=permission_set)
        perm_set_dict[perm_description["PermissionSet"]["Name"]] = permission_set
    return perm_set_dict   

def list_aws_accounts():
    account_list = []
    org_client = boto3.client('organizations')
    paginator = org_client.get_paginator('list_accounts')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        for acct in page['Accounts']:
            # only add active accounts
            
            if acct['Status'] == 'ACTIVE':
        
                
                data = {
                    'name': acct['Name'], 
                    'id': acct['Id'],
                    'content': None
                }
                
                tags = org_client.list_tags_for_resource(ResourceId=acct['Id'])['Tags']
                
                print(tags)
            
                for tag in tags:

                    if tag.get("Key") == TAG_KEY:
                        data[TAG_KEY] = tag["Value"]
                        break
            
                account_list.append(data)
                
    return account_list
    
def lambda_handler(event, context):
    print("DEBUG: Got event:")
    print(event)
    sso_admin_client = boto3.client('sso-admin')
    SNS_TOPIC = os.getenv('SNS_TOPIC')
    sns = boto3.resource('sns')
    topic = sns.Topic(SNS_TOPIC)
    try:
        #org_client = boto3.client('organizations')
        group_display_name = event['detail']['responseElements']['group']['displayName']
        print ("DEBUG: Recieved CreateGroup Event for roup name '{}'".format(group_display_name))
        if not re.match(g_account_pattern, group_display_name):
            print("FAILURE: Security group '{}' does not matching naming convention for account assignment".format(group_display_name))
            return
        
        result=re.search(g_account_pattern, group_display_name)
        account_tag = result.group(1) 
        short_name_pset=result.group(2) 
        if short_name_pset not in PSET_NAME_MAPPING_DICT.keys():
            print("FAILURE: Short name {} for permission set is not known".format(short_name_pset))
            return
        permission_set_name=PSET_NAME_MAPPING_DICT[short_name_pset]
        print("DEBUG: Searching for account '{}' and permission set '{}'".format(account_tag,permission_set_name))
        
        accounts=list_aws_accounts()
        print("DEBUG: List of accounts:", accounts)
        sso_instances=list_sso_instances()
        for sso_instance in sso_instances:
            instance_arn=sso_instance['instanceArn']
            permissionsets=list_permission_sets(instance_arn) #only one SSO instance is supported by AWS SSO at this time
            
        print("DEBUG: Permission sets found {}".format(permissionsets))
        
        account_id, permission_set_arn, account_name = None, None, None
        for a in accounts:
            if a.get(TAG_KEY) == account_tag:
                print("Id of desired account is '{}' ".format(a['id']))
                account_id = a.get('id')
                account_name = a.get('name')
        
        if account_id is None:
            print("FAILURE: Cant find desired accout '{}'".format(account_tag))
            raise Exception("Example Exception for Testing SSO")
    
        for name,arn in permissionsets.items():
            if name == permission_set_name:
                print("ARN of desired permission set is '{}'".format(arn))
                permission_set_arn = arn

        if permission_set_arn is None:
            print("FAILURE: Can't find desired permission set '{}'".format(permission_set_arn))
            return
        principal_id = event['detail']['responseElements']['group']['groupId']
        print("PrincipalId of the group is '{}'".format(principal_id))
        request = {
            "InstanceArn": instance_arn,
            "TargetId": account_id,
            "TargetType": 'AWS_ACCOUNT',
            "PermissionSetArn": permission_set_arn,
            "PrincipalType": 'GROUP',
            "PrincipalId": principal_id,
        }
        cracct_response=sso_admin_client.create_account_assignment(**request)
        cracct_request_id=cracct_response["AccountAssignmentCreationStatus"]['RequestId']
        ps_prov_set_status = sso_admin_client.describe_account_assignment_creation_status(
            InstanceArn=instance_arn,
            AccountAssignmentCreationRequestId=cracct_request_id)
        status=ps_prov_set_status['AccountAssignmentCreationStatus']['Status']
        print("SUCCESS: Security Group '{}' assigned to Account '{}' with permission set '{}'".format(group_display_name, account_name, permission_set_name))
    except Exception as e:
        print(str(e))
        message = {
            "error": str(e),
            "event": event
        }
        topic.publish(
            Message=json.dumps(message),
            Subject="AWS Account Vending Operation Failed: SSO EJS"
        )
        print("Error notification sent via SNS")
      
    
    
