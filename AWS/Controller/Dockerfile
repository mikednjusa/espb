# Dockerfile for Elasticsearch Benchmark Controller, ES Rally and Elasticsearch Monitoring
# 
# VERSION               0.1

# Elasticsearch docker container runs Centos7
# Need to assume that controller scripts were added to the instance via user data when spun up by CF 

#######################################################################################################
# Controller
FROM centos
ENV USERNAME username
ENV PASSWORD password
RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development
RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN python get-pip.py
RUN pip install --upgrade --user awscli
# Install git
RUN yum -y install git git-2.7.4

# Install discovery-ec2 plugin
RUN bin/elasticsearch-plugin install -b discovery-ec2
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN git clone https://$USERNAME:$PASSWORD@github.com/mikednjusa/espb.git
RUN yum -y install unzip
RUN unzip /espb/test_es12.zip 
#RUN python test_executor.py --data_file install_scripts/data_file.json

