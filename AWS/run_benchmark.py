import argparse
import os
import sys
import threading
import json
import collections
import requests
import boto3
import ConfigParser, os

from ES_Test import ES_Test

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

def run_single_test(test_suite_name, name, region, instance_type, security_group_ids, test,
                    root_size_gb, rally_config, save_on_failure=False, debug=True, **kwargs):
  es_test = ES_Test(test_suite_name=test_suite_name,
                    name=name,
                    region=region,
                    instance_type=instance_type,
                    security_group_ids=security_group_ids,
                    test=test,
                    root_size_gb=root_size_gb,
                    rally_config=rally_config,
                    save_on_failure=save_on_failure,
                    debug=debug)
  print('running tests...')
  es_test.run_tests()


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
        ys.exit(1)

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

  # make edits to Cloudformation template
  with open('benchmark.template', 'r') as cffile:
    data=cffile.read()
    data.replace('NUM_INSTANCES', num_instances)
    data.replace('INSTANCE_TYPE', instance_type)
    data.replace('KEY_PAIR', key_pair)
    data.replace('S3_BUCKET', s3_bucket)

    with open("benchmark.yml", "w") as text_file:
      text_file.write(data)
      text_file.close()
    cffile.close()

  # start cloudformation stack
  response = boto3.client('ec2').create_stack(StackName='ES-Benchmarking-Stack', \
                TemplateBody='benchmark.yml')
