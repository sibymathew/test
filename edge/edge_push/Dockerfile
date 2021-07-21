FROM ubuntu:20.04
MAINTAINER siby.mathew@vilimpu.ai

RUN apt-get update -y
RUN apt-get install -y python3-pip

ADD ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD ./note.py /note.py
ADD ./edge_loader.py /edge_loader.py

ENTRYPOINT ["/usr/bin/python3", "note.py"]
