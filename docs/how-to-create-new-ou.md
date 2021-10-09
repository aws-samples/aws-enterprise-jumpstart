# Guide - How to create new Organizational Unit

## Walk-Through
1. Make decision on new OU name, e.g. `sandbox`
2. Create new Organizational Unit within AWS Organizations Console 
3. Create AWS Systems Manager Parameter with OU ID as value: `/org/organization-unit/<ou-name>`

## Usage

Resolve new organization unit id within AWS CloudFormation using dynamic references (`{resolve:ssm:/org/organization-unit/<ou-name>`)

Example:
```yaml
Account:
  Type: ProServe::Organizations::Account
  Properties:
    AccountName: !Ref AccountName
    AccountEmail: !Ref AccountEmail
    OrganizationalUnitId: '{{resolve:ssm:/org/organization-unit/dev}}'
    NotificationTopicArn: !ImportValue notification-topic-arn
    Tags:
    - Key: type
      Value: dev
```
