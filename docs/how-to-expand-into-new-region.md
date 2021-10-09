# Guide - How to expand Enterprise Jumpstart into new AWS Regions

## Walk-Through

1. Adapt `OrgRegions` parameter in every `.json` file within the [/parameter](/parameter) folder
2. Push changes to repository
3. Observe pipeline execution
4. Run the bulk account upgrade AWS CodeBuild project for all organizational units, see [how-to-upgrade-all-accounts.md](how-to-upgrade-all-accounts.md)
5. Verify all accounts are upgraded successfully
