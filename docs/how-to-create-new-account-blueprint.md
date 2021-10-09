# Guide - How to create a new account blueprint

## Pre-requisites

* Create new Organizational Unit for blueprint
  * Create AWS Systems Manager Parameter with OU ID as value: `/org/organization-unit/<ou-name>` 
* Create new Service Control Policy - see separate How To Guide

## Walk-Through
1. Make decision on name of new blueprint, e.g. `sandbox` 
2. Create new file with scheme `<name>.yaml` within `blueprints` folder similar to existing blueprints
3. Add required AWS CloudFormation resources to initial version
4. Add new blueprint to `blueprints/metadata.yaml` file with initial version
5. Create a new product resource within `blueprints/portfolio.yaml` template
   1. Product itself with dummy version: `AWS::ServiceCatalog::CloudFormationProduct`
   2. Assignment to portfolio: `AWS::ServiceCatalog::PortfolioProductAssociation`
   3. Assign AWS Service Catalog Launch Role as launch constraint: `AWS::ServiceCatalog::LaunchRoleConstraint`
   4. Add output to template with `!Ref` to new product as value
6. Adapt `UpdateBlueprints` action environment variables `deployment/pipeline.yaml` to pass new product id
   1. Update pipeline stack with new template
7. Push changes to repository

 