#!/bin/bash
set -e # Fail on any error

# Tweak the env var for sudo:
echo "Tweaking /etc/sudoers to add /usr/local/bin to PATH for sudo..."
sudo cp /home/ec2-user/install_scripts/sudoers /etc/sudoers
sudo chmod 0440 /etc/sudoers

echo "Tweaking vm.max_map_count for ES..."
sudo sysctl -w vm.max_map_count=262144

echo "Installing gcc, openssl, java..."
sudo yum -y install gcc
sudo yum -y install openssl-devel
sudo yum -y install libffi-devel
sudo yum -y install java-1.8.0-openjdk-1.8.0.111
sudo yum -y install java-1.8.0-openjdk-devel-1.8.0.111
sudo alternatives --install /usr/bin/java java /usr/lib/jvm/java-1.8.0-openjdk.x86_64/bin/java 50
sudo alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-1.8.0-openjdk.x86_64/bin/javac 50
sudo alternatives --install /usr/lib/jvm/java-1.8.0 java_sdk_1.8.0 /usr/lib/jvm/java-1.8.0 50

echo "Installing git..."
sudo yum -y install git git-2.7.4

echo "Installing python3..."
sudo yum -y install python34-3.4.3
sudo yum install -y python34-devel-3.4.3

echo "Installing pip3..."
wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py
sudo python3.4 get-pip.py

echo "Installing esrally..."
sudo pip3 install esrally==0.4.8

echo "All done!"
