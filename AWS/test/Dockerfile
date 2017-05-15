# Dockerfile for Elasticsearch Benchmark Controller, ES Rally and Elasticsearch Monitoring
# 
# VERSION               0.1

# Elasticsearch docker container runs Centos7
# Need to assume that controller scripts were added to the instance via user data when spun up by CF 

# ES Rally
FROM docker.elastic.co/elasticsearch/elasticsearch:5.4.0
ENV USERNAME pikeabot
ENV PASSWORD K1llallhumans

USER root
RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development

RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN python get-pip.py

# Install git
RUN yum -y install git git-2.7.4
RUN git clone https://$USERNAME:$PASSWORD@github.com/mikednjusa/espb.git
RUN yum -y install unzip
RUN unzip espb/test_es12.zip 

# Tweak the env var for sudo
RUN cp test_es/install_scripts/sudoers /etc/sudoers
RUN chmod 0440 /etc/sudoers

# Tweak vm.max_map_count for ES
#RUN sysctl -w vm.max_map_count=262144
RUN /bin/sh -c 'echo vm.max_map_count=262144 >> /etc/sysctl.d/sysctl.conf'

# Install gcc, openssl, java
RUN yum -y install gcc
RUN yum -y install openssl-devel
RUN yum -y install libffi-devel
RUN yum -y install java-1.8.0-openjdk
RUN yum -y install java-1.8.0-openjdk-devel
RUN alternatives --install /usr/bin/java java /usr/lib/jvm/java-1.8.0-openjdk.x86_64/bin/java 50
RUN alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-1.8.0-openjdk.x86_64/bin/javac 50
RUN alternatives --install /usr/lib/jvm/java-1.8.0 java_sdk_1.8.0 /usr/lib/jvm/java-1.8.0 50

RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm
RUN yum -y install python36u
RUN yum -y install python36u-pip
RUN yum -y install python36u-devel

# Install git
RUN yum -y install git git-2.7.4

# Install AWS CLI
RUN pip install --upgrade --user awscli

# Installing pip3
#RUN wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py
#RUN python3.6 get-pip.py

#RUN apk add --update --no-cache git build-base linux-headers python-dev openjdk8
RUN pip3.6 install esrally
#COPY rally.ini /root/.rally/

USER elasticsearch