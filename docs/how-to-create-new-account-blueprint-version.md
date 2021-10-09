# Guide - How to create new Account Blueprint Version

## Walk-Through
1. Adapt blueprint Cloudformation template
2. Add new work in progress version to `blueprints/metadata.yaml`
3. Push changes, wait for pipeline so succeed
4. Test new version by upgrading existing non-production account to new version
5. Once all required updates are done, use new version to deploy new accounts

## Upgrade of all accounts
It might be necessary to upgrade all existing accounts to the newly created version.
Please refer to the separate how to guide to upgrade all existing accounts to newest version.
