#!/usr/bin/env bash

set -e

export ARTIFACT_BUCKET_NAME=$1
export ARTIFACTS_BUCKET_PREFIX=$2
python3 scripts/upload_stackset_assets.py
aws cloudformation package --template-file build/pre-packaged.yaml --s3-bucket "$ARTIFACT_BUCKET_NAME" --s3-prefix "$ARTIFACTS_BUCKET_PREFIX" --output-template-file build/packaged-template-baseline.yaml
aws cloudformation package --template-file templates/automation.yaml --s3-bucket "$ARTIFACT_BUCKET_NAME" --s3-prefix "$ARTIFACTS_BUCKET_PREFIX" --output-template-file build/packaged-template.yaml
if [ "$PACKAGE_NORTH_VIRGINIA" == 'true' ]; then aws cloudformation package --template-file templates/org-management-us-east-1.yaml --region us-east-1 --s3-bucket "$ARTIFACTS_BUCKET_NAME_US_EAST_1" --s3-prefix "$ARTIFACTS_BUCKET_PREFIX" --output-template-file build/packaged-template-us-east-1.yaml; fi;
