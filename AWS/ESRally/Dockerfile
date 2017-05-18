# Dockerfile for ES Rally
# VERSION               0.1

# Elasticsearch docker container runs Centos7
# Need to assume that controller scripts were added to the instance via user data when spun up by CF 

# ES Rally -converted from install.sh
FROM docker.elastic.co/elasticsearch/elasticsearch:5.4.0
ENV USERNAME username
ENV PASSWORD password

USER root
RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development
RUN export LC_ALL="en_US.UTF-8"

RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN python get-pip.py

# Modifying /etc/sysctl.conf
# may need to only do this on the instance and not in docker
#COPY sysctl.conf /etc

# Install gcc, openssl, java
RUN yum -y install gcc 
RUN yum -y install openssl-devel
RUN yum -y install libffi-devel
RUN yum -y install java-1.8.0-openjdk
RUN yum -y install java-1.8.0-openjdk-devel
RUN alternatives --install /usr/bin/java java /usr/lib/jvm/java-1.8.0-openjdk.x86_64/bin/java 50
RUN alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-1.8.0-openjdk.x86_64/bin/javac 50
RUN alternatives --install /usr/lib/jvm/java-1.8.0 java_sdk_1.8.0 /usr/lib/jvm/java-1.8.0 50

# Install git 
# https://tecadmin.net/install-git-2-x-on-centos-rhel-and-fedora/#
RUN yum -y install curl-devel expat-devel gettext-devel zlib-devel
RUN yum -y install perl-ExtUtils-MakeMaker
#RUN cd /usr/src
RUN wget https://www.kernel.org/pub/software/scm/git/git-2.7.4.tar.gz
RUN tar xzf git-2.7.4.tar.gz
RUN cd git-2.7.4
RUN make prefix=/usr/local/git all
RUN make prefix=/usr/local/git install
RUN export PATH=/usr/local/git/bin:/usr/local/git:$PATH
RUN source /etc/bashrc

# pull test info
RUN git clone https://$USERNAME:$PASSWORD@github.com/mikednjusa/espb.git
RUN yum -y install unzip
RUN unzip espb/test_es12.zip 

# Tweak the env var for sudo
RUN cp test_es/install_scripts/sudoers /etc/sudoers
RUN chmod 0440 /etc/sudoers

# Install AWS CLI
RUN pip install --upgrade --user awscli

# Install discovery-ec2 plugin
RUN bin/elasticsearch-plugin install -b discovery-ec2
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Installing python3
RUN yum -y install epel-release
RUN yum -y install python34
RUN yum install -y python34-devel

# Installing pip3
RUN yum install -y python34-setuptools
RUN easy_install-3.4 pip

# Installing esrally
RUN pip3 install esrally==0.4.8

USER elasticsearch
