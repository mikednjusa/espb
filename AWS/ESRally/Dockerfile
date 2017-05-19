# Dockerfile for ES Rally
# VERSION               0.1

# Elasticsearch docker container runs Centos7
# Need to assume that controller scripts were added to the instance via user data when spun up by CF 

# ES Rally -converted from install.sh
FROM centos

USER root
RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development
RUN yum -y install nano
# Necessary to add this or esrally throws an error
RUN echo export LC_ALL="en_US.UTF-8" >> /root/.bashrc

RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN python get-pip.py

# Install gcc, openssl, java
RUN yum -y install gcc 
RUN yum -y install openssl-devel
RUN yum -y install libffi-devel
RUN yum -y install java-1.8.0-openjdk
RUN yum -y install java-1.8.0-openjdk-devel
RUN alternatives --install /usr/bin/java java /usr/lib/jvm/java-1.8.0-openjdk.x86_64/bin/java 50
RUN alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-1.8.0-openjdk.x86_64/bin/javac 50
RUN alternatives --install /usr/lib/jvm/java-1.8.0 java_sdk_1.8.0 /usr/lib/jvm/java-1.8.0 50

# Install git 2.7.4. Esrally requires git > = 1.9
# https://tecadmin.net/install-git-2-x-on-centos-rhel-and-fedora/#
RUN yum -y install curl-devel expat-devel gettext-devel zlib-devel
RUN yum -y install perl-ExtUtils-MakeMaker
RUN yum install -y wget
RUN wget https://www.kernel.org/pub/software/scm/git/git-2.7.4.tar.gz
RUN tar xzf git-2.7.4.tar.gz
RUN make -C /git-2.7.4 prefix=/usr/local/git all
RUN make -C /git-2.7.4 prefix=/usr/local/git install
RUN export PATH=/usr/local/git/bin:/usr/local/git:$PATH
RUN source /etc/bashrc

# Installing python3
RUN yum -y install epel-release
RUN yum -y install python34
RUN yum install -y python34-devel

# Installing pip3
RUN yum install -y python34-setuptools
RUN easy_install-3.4 pip

# Installing esrally
RUN pip3 install esrally==0.4.8


