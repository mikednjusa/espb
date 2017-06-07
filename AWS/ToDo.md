## To Do:

1. Add AWS networking, i.e. VPC, subnet, security groups etc. 
2. Pull the monitoring logs to S3
3. Save CSV files to S3
4. Run multiple tests and check if threading will be needed
5. Make sure volume stores are set up correctly 
6. Reorganize S3 logging buckets so it's not just a data dump
7. Look into using the Docker Python API again
8. Add teradown option?

### Finished: 

1. Dockerfiles for elasticsearch, kibana and esrally
  - Needed to create custom Dockerfiles for all three
  - elasticsearch needed discovery-ec2 plugin
  - kibana needs custom kibana.yml config file to set elasticsearch url
  - No updated esrally docker image exists so must build from file
2. Docker compose files for benchmarking and esrally/monitoring 
  - Needed to figure out the networking portions of it to create a cluster
3. Basic AWS Cloudformation template to set up Docker containers and run tests
  - Ran into issues with running bash commands via python. Needed extra commands, i.e.
  chown and chmod that aren't necessary if running from command line.
  - Containers take time to spin up and checks needed to be added
4. Wrote run scripts for user as well as the python script to run the testing
5. Finish configuring and debugging the elasticsearch monitoring
6. Fix esrally metrics store setup
