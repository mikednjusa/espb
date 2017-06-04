# Dockerfile from esbuildy/docker-esrally
# Set up an esrally docker image

FROM java:8

RUN apt-get update && \
    apt-get install -y \
                python3 \
                python3-pip \
                git

RUN pip3 install esrally

RUN apt-get clean && \
        rm -rf /var/lib/apt/lists/*

RUN useradd  -m -s /bin/bash es

RUN mkdir /home/es/.rally
RUN chown -R es:es /home/es/.rally

USER es

WORKDIR /home/es