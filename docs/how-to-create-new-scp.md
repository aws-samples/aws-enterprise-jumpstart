# Guide - How to create a new Service Control Policy (SCP)

## Walk-Through
1. Make decision on name of SCP, such as `sandbox` to match the organizational unit name or purpose
2. Create file with scheme `<scp-name>.json` within `scps` folder
3. Add new SCP within `metadata.yaml` file, targets support OU IDs or 12-digit AWS Account IDs
4. Push changes, the SCP will be created and attach to given organzational unit id

## Hints
Service Control Policies are never deleted or detached by the `DeployScps` action within CodePipeline
