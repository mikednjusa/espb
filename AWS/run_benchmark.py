import argparse
import os
import sys
import json
import collections
import requests
import boto3
import ConfigParser
import re

# Parse command line args:
def parseArgs():
  description = '''
    HVM instance type matrix for linux ami:
    https://aws.amazon.com/amazon-linux-ami/instance-type-matrix/
    List of all instance types:
    http://www.ec2instances.info/
  '''
  parser = argparse.ArgumentParser(description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--data_file', help='If set, script will read that file to create instances.', required=True)
  parser.add_argument('--config_file', help='If set, script will read that file to create instances.', required=True)

  args = parser.parse_args()

  if not os.path.exists(args.data_file):
    print('***Error: File does not exist: {}'.format(args.data_file))
    sys.exit(1)

  if not os.path.exists(args.config_file):
    print('***Error: File does not exist: {}'.format(args.config_file))
    sys.exit(1)
  return args

if __name__ == '__main__':
  version = '0.0.1'
  print('Version: {}'.format(version))
  args = parseArgs()
  # If creating multiple ES_Test objects, make sure name is unique.
  # The name is used to create unique directories, etc.
  with open(args.data_file) as df:
    try:
      data = json.load(df)
    except:
      print('***Error: The following file is not a valid json file: {}'.format(args.data_file))
      sys.exit(1)

  # Do some basic validation against the json:
  for test_suite, tests in data['test_suites'].items():
    seen = set()
    for test in tests:
      if test['name'] in seen:
        print('Error: duplicate test name found in data file: {}'.format(test))
        sys.exit(1)
      seen.add(test['name'])

  # parse config file
  config = ConfigParser.ConfigParser()
  config.read(args.config_file)
  num_instances = config.get('esrally', 'NUM_OF_INSTANCES')
  instance_type = config.get('esrally', 'INSTANCE_TYPE')
  key_pair = config.get('esrally', 'INSTANCE_KEY_PAIR')
  s3_bucket = config.get('esrally', 'S3_BUCKET')
  region = config.get('esrally', 'REGION')
  
  # make edits to Cloudformation template
  with open('benchmark.template', 'r') as cffile:
    data=cffile.read()
    #data = re.sub('NUM_INSTANCES', num_instances)
    data = re.sub('INSTANCE_TYPE', instance_type, data)
    data = re.sub('INSTANCE_KEY_PAIR', key_pair, data)
    data = re.sub('S3_BUCKET', s3_bucket, data)
    data = re.sub('DATA_FILE_S3_LOCATION', s3_bucket, data)
    data = re.sub('REGION', region, data)
    cffile.close()

  with open("benchmark-cf.yml", "w") as text_file:
    text_file.write(data)
    text_file.close()

  # push the test file to S3
  response = boto3.client('s3').upload_file(args.data_file, s3_bucket, 'data_file.json')
  # upload edited cloudformation template to S3
  response = boto3.client('s3').upload_file('benchmark-cf.yml', s3_bucket, 'benchmark-cf.yml')
  
  # start cloudformation stack
  templateUrl = 'https://s3.amazonaws.com/{0}/benchmark-cf.yml'.format(s3_bucket)
  response = boto3.client('cloudformation').create_stack(StackName='ES-Benchmarking-Stack', \
            TemplateURL=templateUrl)