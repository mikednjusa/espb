# Elasticsearch Benchmark Dockerfile

FROM docker.elastic.co/kibana/kibana:5.4.0

USER root
RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development

RUN docker cp /home/ec2-user/espb/AWS/ESRally/kibana/kibana.yml kibana:/usr/share/kibana/config/kibana.yml
