FROM ubuntu:xenial

MAINTAINER Vasif Syed <vsyed@brocade.com>

ARG BUILD_DATE

# Upgrading apt-get
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
RUN apt-key adv --keyserver hkps.pool.sks-keyservers.net --recv-keys 0x6B73A36E6026DFCA
RUN echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.4.list
#RUN echo 'deb http://www.rabbitmq.com/debian/ stable main' | tee /etc/apt/sources.list.d/rabbitmq.list
RUN apt-get update

## Installing required apt-get packages
#RUN apt-get install -y openssl
RUN apt-get install -y cron
RUN apt-get install -y supervisor 
RUN apt-get install -y mosquitto mosquitto-clients 
RUN apt-get install -y mongodb-org-server
RUN apt-get install -y --allow-unauthenticated rabbitmq-server
RUN apt-get install -y python3 python3-pip
RUN apt-get clean

# Python Modules install.
RUN pip3 install --upgrade pip

ADD VRIOT /VRIOT

# Installing application specific requirements
WORKDIR /VRIOT/ops/docker/webservice
RUN pip3 install -r requirement.txt
WORKDIR /VRIOT/backend
RUN pip3 install -r requirement.txt

# Download and Install Nginx
RUN apt-get install -y nginx
# Remove the default Nginx configuration file
RUN rm -v /etc/nginx/nginx.conf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
# Copy a configuration file from the current directory
COPY nginx.conf /etc/nginx/

# making required directories for Mongo DB
RUN mkdir -p /data/db /data/log
# Append "daemon off;" to the beginning of the configuration
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# Adding necessary config and certificate files into docker
COPY mongod.conf /etc/
COPY logrotate.conf /etc/
COPY logrotate.d /etc/logrotate.d
COPY certs/ca.crt /VRIOT/backend/certs/mqtt/
COPY certs/ /etc/mosquitto/certs/
COPY mosquitto.conf /mqtt-broker/

# Adding CA files into the docker
COPY certs/ca.crt /cafiles/
COPY certs/ca.key /cafiles/

EXPOSE 27017 8000 8883 9001 5672 5000 5216 1883 8080 80
VOLUME ["/data"]

ENTRYPOINT ["/usr/bin/python","/VRIOT/ops/scripts/entrypoint.py"]