# Guide - How to enroll exsting account into EJS account cloud foundation

## Walk-through
1. Note down AWS Account Id and Email
2. Double-check **properties** section of `Account` resource

The the `/blueprints/dummy-import.yaml` template. The properties of the `Account` have to match the properties configured within the same resource within the Account Blueprint you like to enroll the existing AWS account into.

3. Within AWS Service Catalog launch the account blueprint desired for the existing account with the parameters matching the existing account and desired state.

**!Important** Choose the `dummy` version of the blueprint AWS Service Catalog product. This will not actually create an account, rather then just launching a __empty__ product.

**!Important** Email address and account name have to match the existing account email and name.

4. Navigate to AWS Cloudformation console and the stack created by step 3.
5. Navigate to Stack Actions -> Import resources into stack
6. Choose to upload a template and pick file `/blueprints/dummy-import.yaml` from your disk, click next
7. Paste the account id of the existing account you like to import and proceed with importing
8. Wait for the Cloudformation stack shows import complete. For troubleshooting see Cloudformation event error messages and check AWS Cloudwatch log group `Proserve-Organizations-Account`.
9. Navigate to AWS Service Catalog Provisioned Product, find the provisioned product launched in step 3. and update it to the newest version of your blueprint

## Hints

Before actually importing the resource, Cloudformation will perform a read operation on the resource. This ensures the acccount exists.

Any failure with important has **no** impact to the account itself. There is no resource touched within the account in this process. The `DeploymentAccountConfiguration` property is only respected on creation, the role has to be created manually if you import the account.

The deletion policy `retain` ensures the account is not moved to root OU on failure of import.

