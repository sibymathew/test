#!/bin/sh

version=$1

docker push sibymath/circletest:$version

EB_S3_BUCKET=siby-circletest-s3
aws s3 cp Dockerrun.aws.json s3://$EB_S3_BUCKET/Dockerrun.aws.json

aws elasticbeanstalk create-application-version --application-name siby-circletest --version-label $version --source-bundle S3Bucket=$EB_S3_BUCKET,S3Key=Dockerrun.aws.json

aws elasticbeanstalk update-environment --environment-name siby-circletest-env --version-label $version
