## How to Run the Benchmarks

### Requirements:
  * Python 2.7+
  * Docker
  * AWS User with access keys and AWS CLI set up already
  * S3 Bucket
  * Instance key pair

Python Libraries:
  * boto 1.4.4
  * ConfigParser
  * requests

### Usage:

```
python run_benchmark.py –config_file <config-file> --data_file <JSON data file>
```
The script will take in a config file and set up the benchmarking cluster and monitoring. It will use the data file to run the esrally benchmarking test. After the benchmarking is done, it will save the data to an S3 bucket and then tear itself down. 

**Note: It does take several minutes for the Docker containers to come up and be running**

### How To Run:

1. Pull the docker image pikeabot/docker-controller. This container has the latest github code from the benchmark branch as well as all of the libraries and dependencies already installed. https://hub.docker.com/r/pikeabot/docker-controller/
```
docker pull pikeabot/docker-controller
```
2. Start a docker container and then run the container bash
```
docker run -dit --name docker-controller pikeabot/docker-controller 
docker exec -it docker-controller /bin/bash
```
3. In the container, run aws configure and enter your aws credentials
```
$ aws configure
```

4. cd /home/espb/AWS

5. Update the config.example to include your S3 bucket, key pair name, github username and password, the number of instances, the region and instance type.

6. run:
```
python run_benchmark.py --config_file <config-file> --data_file <JSON data file>
```
You should see 'Version: 0.0.1' and no errors. 

7. If you log into AWS, under Cloudformation you should see ES-Benchmarking-Stack

8. The script takes at while to run and it takes several minutes to create the docker images and launch the containers.

9. If there are any errors, there are several log files you can check such as /var/log/cloud-init-output.log for any errors during bootrapping. The output of run_test.py (the script that runs the esrally benchmarking and saves the log files to S3) logged at /home/ec2-user/espb/AWS/logging.out on the EsRally-Monitoring instance. 

For whatever reason, the esrally benchmarking command sometimes hangs. I think this has to something to do with using python subprocess to call bash commands from run_test.py in the ESRally folder. You can either wait or delete the stack and start over.
