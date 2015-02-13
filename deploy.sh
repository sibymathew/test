#!/bin/sh

VERSION=v1
APP_NAME=siby-circletest3
ENV_NAME=siby-circletest3-env

docker push sibymath/circletest:$version

aws configure set region us-west-2

EB_S3_BUCKET=siby-circletest-s3
aws s3 cp content.zip s3://$EB_S3_BUCKET/content.zip
aws s3 cp dockercfg s3://$EB_S3_BUCKET/docker/dockercfg

aws elasticbeanstalk create-application --application-name $APP_NAME
aws elasticbeanstalk create-application-version --application-name $APP_NAME --version-label $VERSION --source-bundle S3Bucket=$EB_S3_BUCKET,S3Key=content.zip

sleep 10

aws elasticbeanstalk create-environment --environment-name $ENV_NAME --application-name $APP_NAME --solution-stack-name "64bit Amazon Linux 2014.09 v1.0.11 running Docker 1.3.3" --cname $ENV_NAME --option-settings file://options.txt

sleep 150

aws elasticbeanstalk describe-applications

sleep 150

aws elasticbeanstalk describe-environments

sleep 100

aws elasticbeanstalk update-environment --environment-name $ENV_NAME --version-label $VERSION
