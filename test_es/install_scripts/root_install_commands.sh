#!/bin/bash
set -e # Fail on any error

echo "Modifying /etc/sysctl.conf..."
echo "fs.file-max = 512000" >> /etc/sysctl.conf
echo "vm.max_map_count = 262144" >> /etc/sysctl.conf

echo "Modifying /etc/security/limits.conf..."
echo "* - nofile 65536" >> /etc/security/limits.conf
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

echo "Modifying start time for rally..."
sed -c -i "s/\(PROCESS_WAIT_TIMEOUT_SECONDS *= *\).*/\140/" /usr/local/lib/python3.4/site-packages/esrally/mechanic/launcher.py
echo "All done!"
