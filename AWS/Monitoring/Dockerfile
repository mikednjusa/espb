# Dockerfile for Elasticsearch Monitoring
# 
# VERSION               0.1

# Elasticsearch docker container runs Centos7
# Need to assume that controller scripts were added to the instance via user data when spun up by CF 

# Can use this for monitoring and benchmark instances?

FROM docker.elastic.co/elasticsearch/elasticsearch:5.4.0

USER root
RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development

RUN yum -y install epel-release
RUN yum -y install python34
RUN yum install -y python34-setuptools
RUN easy_install-3.4 pip

RUN yum -y install wget gcc git python34-devel 

# Modifying /etc/sysctl.conf
COPY sysctl.conf /etc

# Install discovery-ec2 plugin
RUN bin/elasticsearch-plugin install -b discovery-ec2
COPY docker-entrypoint.sh /docker-entrypoint.sh

USER elasticsearch