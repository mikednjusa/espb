# Elasticsearch Benchmark Dockerfile

FROM docker.elastic.co/elasticsearch/elasticsearch:5.4.0

USER root
RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development

RUN bin/elasticsearch-plugin install -b discovery-ec2

USER elasticsearch