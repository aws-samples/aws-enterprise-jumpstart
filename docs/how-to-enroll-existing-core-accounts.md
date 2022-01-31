# Guide - How to enroll exsting core accounts into EJS account cloud foundation

This guide is intended to help enrolling existing audit and log accounts. This is mainly required if the initial deployment of Enterprise Jumpstart failed. If you have existing accounts for this purpose please consider to create new ones and they are baselines during the enterprise jumpstart deployment.


## Walk-through
AWS CloudFormation will automatically incorporate the existing account and read the required metadata via AWS API. It will apply tags as defined in CloudFormation and move the account into the choosen organizational unit within AWS Organizations.

That said, you can adapt the account information in [/parameter/core-accounts.json](/parameter/core-accounts.json) and rerun the EJS main pipeline. This will incorporate the accounts if email and name matches.

## Hints

Cloudformation will perform a read operation on the resource. This ensures the acccount exists and matches name and email.

Any failure with important has **no** impact to the account itself. There is no resource touched within the account in this process. The `DeploymentAccountConfiguration` property is only respected on creation, but it will not override existing configurations.

The account is moved to root OU on failure of enrollment.