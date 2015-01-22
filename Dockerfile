FROM ubuntu:14.04

# Update packages
RUN apt-get update -y

# Install Python Setuptools
RUN apt-get install -y python-setuptools curl

# Install pip
RUN easy_install pip

# Add and install python modules
ADD requirements1-txt /docker/requirements-txt
RUN cd /docker; pip install -r requirements-txt

# Bundle app source
ADD . /docker

# Expose
EXPOSE 5000

# Run

CMD ["python", "docker/src/application.py"]
