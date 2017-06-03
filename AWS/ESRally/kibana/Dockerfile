# Elasticsearch Benchmark Dockerfile

FROM docker.elastic.co/kibana/kibana:5.4.0
COPY kibana.yml /usr/share/kibana/config/kibana.yml
USER root
RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development

