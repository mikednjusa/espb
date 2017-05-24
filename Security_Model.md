# Security for ES Rally Benchmarking

The benchmarking instances will have its own VPC, default public and private subnets, and custom security group. 

The security group policy will be set to the minimum number of permissions: ec2, s3 access. 
Jon's current security group:


IAM roles and instance profiles will also be created for further isolation. 

The controller/esrally and monitoring instance will be set in a public subnet so that Kibana can be reached. 
Restrict inbound access to TCP on port 5601 for Kibana - logins should be changed from defaults

(not needed) Because esrally and the controller need to reach Github, there is a potential security issue. This can be mitigated with setting up AWS ingress rules to restrict access, using only approved images as well as setting up Docker security measures such as control groups and namespaces. Whitelisting files and executables can also be implemented if necessary.

?Might need AWS discovery EC2 plugin for ES instances to find cluster members?

(not needed) The benchmarking instances will be put in a private subnet. 

Further security can be applied to the Elasticsearch cluster by adding passwords using X-Pack.

The Cloudformation stack will handle the setting up and tearing down of the networking components. And because it is small and simple and intended to be torn down after testing, it should not add to the overhead of anyone’s system. The stack will create the bucket if it does not exist and a deletion policy will be put in place so that the bucket is not deleted when the stack is. 

? (may be handled by docker compose script from elastic.co) Another reason for wanting to set up a separate VPC is because it allows us to set the IPs for the elasticsearch nodes. This is necessary in order to create a cluster on separate ec2 instances as in order to connect the nodes they need to know the IP of the other node. 

![Security Model](/Security_Model.png)
