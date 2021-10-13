# Guide - How to enroll exsting core accounts into EJS account cloud foundation

This guide is intended to help enrolling existing audit and log accounts. This is mainly required if the initial deployment of Enterprise Jumpstart failed. If you have existing accounts for this purpose please consider to create new ones and they are baselines during the enterprise jumpstart deployment.


## Walk-through
1. Note down AWS Account Id and Email of your Audit and 
4. Navigate to AWS Cloudformation console and the stack created by step 3.
5. Navigate to Create Stack -> With existing resources
6. Choose to upload a template and pick file `/templates/core-accounts-import.yaml` from your disk, click next
7. Give the stack the following name `<ejs-prefix>--core-accounts`
8. Paste the account ids of the existing accounts you like to import and proceed with importing
9. Wait for the Cloudformation stack shows import complete. For troubleshooting see Cloudformation event error messages and check AWS Cloudwatch log group `Proserve-Organizations-Account`.
10. Navigate to AWS Cloudformation console and the stack created in the last steps
11. Cick Update and choose to upload new template, upload `templates/core-accounts.yaml`
12. Wait for update complete status
13. Run Enterprise Jumpstart main pipeline

## Hints

Before actually importing the resource, Cloudformation will perform a read operation on the resource. This ensures the acccount exists.

Any failure with important has **no** impact to the account itself. There is no resource touched within the account in this process. The `DeploymentAccountConfiguration` property is only respected on creation, the role has to be created manually if you import the account.

The deletion policy `retain` ensures the account is not moved to root OU on failure of import.
