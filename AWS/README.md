## How to Run the Benchmarks

### Requirements:
AWS User with access keys and AWS CLI set up already

### Usage:
python run-benchmarking.py –config-file <config-file> --data-file <JSON data file>

The script will take in a config file and set up the benchmarking cluster and monitoring. It will use the data file to run the esrally benchmarking test. After the benchmarking is done, it will save the data to an S3 bucket and then tear itself down. 

**Note: It does take several minutes for the Docker containers to come up and be running**

### Config File:

The script will take in a config file with the following parameters:

NUM_OF_INSTANCES -number of benchmarking instances, max 5

INSTANCE_TYPE -i.e. m4.large

DEDICATED_HOST_ID -if a host id is provided then it will use the dedicated host instead of regular instances

DEDICATED_HOST_INSTANCE_TYPE -i.e. m4.large

NUM_DEDICATED_HOST_INSTANCES -number of benchmarking instances launched on dedicated hosts, max 5

INSTANCE_KEY_PAIR -their desired instance key pair in case they want to be able to access the instances. Otherwise if left blank the script will create an instance key pair. 

S3_BUCKET -the location of the S3 bucket where JSON data will be stored. 

LOCAL_DATA_DIR: Optional local drive to save the JSON data
 
### Data File:

Example: 
{
 
  "test_suites": {
 
    "testsuite_001": [
 
      {
 
        "name": "large_track_tiny1",
 
        "instance_type": "m3.medium",
 
        "security_group_ids": "",
 
        "region": "us-west-2",
 
        "test": "esrally --pipeline=from-distribution --distribution-version=5.0.0 --track=geonames --test-mode",
 
        "rally_config": "conditional_install_items/rally_csv.ini",
 
        "root_size_gb": 16,
 
        "do_run": false,
 
        "save_on_failure": false
 
      }
}
 
