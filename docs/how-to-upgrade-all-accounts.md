# Guide - How to update all existing account within a particular organization unit

## Walk-Through

An AWS CodeBuild project is created to perform this job.
The following AWS CLI command can be used to upgrade all account within a particular organization unit to a specific version.

Three parameters are required:
* ORGANIZATIONAL_UNIT: Organizational Unit Id
* PRODUCT_ID: AWS Service Catalog Product Id (Account Blueprint Product)
* PRODUCT_VERSION_NAME: Version of Account Blueprint

```bash
aws codebuild start-build --project-name <prefix>-account-upgrade --region <home-region> --environment-variables-override \
    name=ORGANIZATIONAL_UNIT,value=<ou-id>,type=PLAINTEXT \
    name=PRODUCT_ID,value=<product-id>,type=PLAINTEXT \
    name=PRODUCT_VERSION_NAME,value=<product-version-name>,type=PLAINTEXT
```