this directory contains docker files and notes on building/customizing our docker files

Docker files needed:
## Name: es-benchmark
Description: This is the elasticsearch instance that is being benchmark tested for performance.

Root image and customizations:
from elastic.co default docker file
configure the instance to be monitored by marvel/monitoring on the es-monitor elasticsearch instance
makes password and config changes
handles communication settings for es cluster if benchmarking multiple-instance cluster

Install jq so we can get raw/disk ratio from the elasticsearch instance
https://stedolan.github.io/jq/

Example docker file from:
https://hub.docker.com/r/frekele/elasticsearch/~/dockerfile/
NOTE this file failed to build. The following command failed and is commented out in the docker file:
 RUN /usr/share/elasticsearch/bin/elasticsearch-plugin remove x-pack

# begin docker file #
FROM docker.elastic.co/elasticsearch/elasticsearch:5.2.2

MAINTAINER frekele <leandro.freitas@softdevelop.com.br>

ADD config/elasticsearch.yml /usr/share/elasticsearch/config/

USER root

#Remove X-Pack
#RUN /usr/share/elasticsearch/bin/elasticsearch-plugin remove x-pack

RUN chown elasticsearch:elasticsearch /usr/share/elasticsearch/config/elasticsearch.yml

USER elasticsearch
# end of example docker file #

## Name: es-monitoring
Description: This is the elasticsearch instance that is monitoring the elasticsaearch instance/cluster that is being benchmark tested for performance.
It uses marvel/monitoring to collect performance data on the es-benchmark instances, as well as receives the detailed rally data from the es-rally instance.

Root image and customizations:
from elastic.co default docker file
configure the instance to use x-pack marvel/monitoring to monitor the es-benchmark elasticsearch instance(s)
makes password and config changes
handles communication settings for es cluster if benchmarking multiple-instance cluster

## Name: rally
Description: This is the rally instance that performs the benchmark test.
The current https://github.com/ebuildy/docker-esrally seems to work. I suggest we clone it and make changes as needed.

Changes: update rally.ini to access the es-benchmark instance/cluster. Also if config changes are needed to send detailed monitoring data to the es-monitor instance, make them.
# begin docker file #
FROM java:8

RUN apt-get update && \
    apt-get install -y \
                python3 \
                python3-pip \
                git

RUN pip3 install esrally

RUN apt-get clean && \
        rm -rf /var/lib/apt/lists/*

RUN useradd  -ms /bin/bash es

USER es

WORKDIR /home/es
# begin docker file #

## Name: controller
Description: This instance will download github files and run processes to: 
Build the AWS resources
Install all components
Run the test 
Monitor the test until completion or failure
Export data to the S3 bucket
Terminate/delete all resources except S3
Self-terminate itself

This instance will need AWS CLI, user keys, python 2.7 or 3
