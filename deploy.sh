#!/bin/sh

version=v3

docker push sibymath/circletest:$version

#cp /home/ubuntu/.aws/credentials /home/ubuntu/.awssecret
#chmod 400 /home/ubuntu/.awssecret
#rm -rf /home/ubuntu/.aws/config
aws configure set region us-west-2

EB_S3_BUCKET=siby-circletest-s3
aws s3 cp Dockerrun.aws.json s3://$EB_S3_BUCKET/Dockerrun.aws.json
aws s3 cp dockercfg s3://$EB_S3_BUCKET/docker/dockercfg

aws elasticbeanstalk create-application-version --application-name siby-circletest --version-label $version --source-bundle S3Bucket=$EB_S3_BUCKET,S3Key=Dockerrun.aws.json

aws elasticbeanstalk update-environment --environment-name sibycircletest-env --version-label $version
