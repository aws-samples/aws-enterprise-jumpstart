# Guide - How to enroll exsting account into EJS account cloud foundation

## Walk-through
Within AWS Service Catalog launch the account blueprint desired for the existing account using the newest version and with the parameters matching the existing account and desired state.

AWS CloudFormation will automatically incorporate the existing account and read the required metadata via AWS API. It will apply tags as defined in CloudFormation and move the account into the choosen organizational unit within AWS Organizations.

## Hints

Cloudformation will perform a read operation on the resource. This ensures the acccount exists and matches name and email.

Any failure with important has **no** impact to the account itself. There is no resource touched within the account in this process. The `DeploymentAccountConfiguration` property is only respected on creation, but it will not override existing configurations.

The account is moved to root OU on failure of enrollment.

