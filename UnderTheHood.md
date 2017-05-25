# Under the Hood

1. The user runs the python script. The input is a desired benchmark config file and a test file.
2. The script will take a cloudformation template and create a stack via AWS CLI or boto (Will probably end up being boto as python gives more control and readability to the code). 
3. The cloudformation stack will spin up all the AWS related components. It will also set up the necessary networking to form the benchmark cluster.
  * VPC
  * IAM roles
  * EC2 instances
  * Security Group
4. The Cloudformation template’s ec2 userdatas will run a bash script that will set up the desired environments. 
  * For the Controller/ES Rally/Monitoring instance:
    1. Install Docker, Git, AWS CLI and pull the git repo
    2. Run docker compose to bring up kibana and esrally (I think the controller script doesn’t need to be in a separate container)
    3. Run the test scripts
  * For the benchmarking instance:
    1. Install Docker, Git and pull the git repo
    2. Run docker compose to bring up the benchmarking instance
5. The testing script will run the desired rally tests specified in the data file. Once it is done, it will save the data from the monitoring instance to the S3 bucket. It will also run a command to delete the cloudformation stack. This will tear down all of the components created -VPC, instances etc. 
