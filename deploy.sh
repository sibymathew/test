#!/bin/sh

docker push sibymath/circletest:v2

cp /home/ubuntu/.aws/credentials /home/ubuntu/.awssecret
chmod 400 /home/ubuntu/.awssecret
echo "[default]" >> /home/ubuntu/.aws/config
echo "us-west-2" >> /home/ubuntu/.aws/config
chmod 400 /home/ubuntu/.aws/config

EB_S3_BUCKET=siby-circletest-s3
aws s3 cp Dockerrun.aws.json s3://$EB_S3_BUCKET/Dockerrun.aws.json

aws elasticbeanstalk create-application-version --application-name siby-circletest --version-label v1 --source-bundle S3Bucket=$EB_S3_BUCKET,S3Key=Dockerrun.aws.json

aws elasticbeanstalk update-environment --environment-name siby-circletest-env --version-label v1
