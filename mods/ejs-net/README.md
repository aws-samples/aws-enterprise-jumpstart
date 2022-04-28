# Enterprise Jumpstart Central Network Components

This repository holds central network components required globally (e.g. Route53 hosted zone) and regional (e.g. Transit Gateway, S2S VPN)

## Quickstart

* Deploy deployment/pipeline.yaml into home region with name `ejs-network-pipeline` and empty additional regions
* Create the following SSM Parameters if not enrolled centrally
	* `/org/management-account/id`
	* `/org/id`
	* `/org/network/domain`
* Enable Resource Manager integration within the Management Account for AWS Organizations
* Push code to codecommit repository and wait for pipline to finish


* Decide which additional regions you want to deploy into by following the guide below, us-east-1 is prepared as an example.

## Guide - How to expand to new region
1. Add new region to `parameter/pipeline.json` parameter value for `AdditionalRegions`
2. Push code and verify pipeline succeeded
3. Add additional artifact store within pipeline definition in `deployment/pipeline.yaml` (`AWS::CodePipeline::Pipeline`)
4. Add parameter file for each regional step for new region similar to `regional.json`, e.g. `regional-eu-central-1.json`
5. Add additional cloudformation deploy action at the end of the pipeline stage `RegionalDeployment` similar to `us-east-1` actions
6. Add parameters mentioned in Quickstart step 2 in addtional regions if not deployed centrally
7. Push Code and verify pipeline is complete

**!Important** Ensure no cloudformation action deploys to the same region and stackname
