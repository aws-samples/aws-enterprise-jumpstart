# Guide - How to merge changes from newest Enterprise Jumpstart Codebase

* Pull file changes from newest version into your repository directory
* Use a diff tool from your choice to double check changes to not override changes done by you
* Be extra carefull with `/parameter` folder, make sure **no** parameter values are overwritten with default values
* Use `git checkout -- <file-name>` on parameter json files if you are sure there is no change required to update

Once you are sure the changes look good, commit changes and push commit to your repository.

## Hints

If errors occur, start troubleshooting from the central Enterprise Jumpstart Codepipeline. Dive deeper to Cloudformation event logs, Codebuild logs, Cloudwatch logs for Cloudformation private registry issues.

## Disclaimer

While changes are carefully throught through, there is no guarantee a change can potentially impact the deployment.
It will not automatically perform changes on workload accounts.