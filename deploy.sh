#!/bin/sh

VERSION=v1
APP_NAME=siby-circletest
ENV_NAME=siby-circletest-env

docker push sibymath/circletest:$version

aws configure set region us-west-2

EB_S3_BUCKET=siby-circletest-s3
aws s3 cp Dockerrun.aws.json s3://$EB_S3_BUCKET/Dockerrun.aws.json
aws s3 cp dockercfg s3://$EB_S3_BUCKET/docker/dockercfg

aws elasticbeanstalk create-application --application-name $APP_NAME
aws elasticbeanstalk create-environment --environment-name $ENV_NAME --application-name $APP_NAME

aws elasticbeanstalk create-application-version --application-name $APP_NAME --version-label $VERSION --source-bundle S3Bucket=$EB_S3_BUCKET,S3Key=Dockerrun.aws.json

aws elasticbeanstalk update-environment --environment-name $ENV_NAME --version-label $VERSION
