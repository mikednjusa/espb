import os
from os import listdir
from os.path import isfile, join
import sys
import threading
import argparse
import json
import collections
import requests
import boto3
import re
import subprocess
import shutil

# Parse command line args:
def parseArgs():
  description = '''
    HVM instance type matrix for linux ami:
    https://aws.amazon.com/amazon-linux-ami/instance-type-matrix/
    List of all instance types:
    http://www.ec2instances.info/
  '''
  parser = argparse.ArgumentParser(description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--bucket', help='If set, script will read that file to create instances.', required=True)
  return parser.parse_args()


def run_single_test(test, bucket):
  #test_params=json.loads(single_test)
  bashCommand = 'docker cp {0} esrally:/home/es/.rally/rally.ini'.format(test['rally_config'])
  run(bashCommand)

  bashCommand = 'docker exec -it -u root esrally chown -R es:es /home/es/.rally'
  run(bashCommand)

  bashCommand = 'docker exec -it esrally {0}'.format(test['test'])
  print bashCommand
  run(bashCommand)
  
  bashCommand = 'docker cp esrally:/home/es/.rally/logs/ /home/ec2-user/espb/AWS/ESRally/logs'
  run(bashCommand)

  return

# General purpose run command:
def run(bashCommand):
  process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
  output, error = process.communicate()
  return


if __name__ == '__main__':
    
  args = parseArgs()
  #boto3.resource('s3').meta.client.download_file(args.bucket, 'data_file.json', 'data_file.json')
  with open('data_file.json') as json_data:
    data = json.load(json_data)

  # Run all tests of a test suite in parallel:
  for test_suite, tests in data['test_suites'].items():
      print('Running test suite: {}'.format(test_suite))
      threads = []
      for test in tests:
          if 'do_run' in test and not test['do_run']:
              print("Skipping: {} in {} because do_run is set to false.".format(test['name'], test_suite))
              continue
          test['test_suite_name'] = test_suite

          run_single_test(test, args.bucket)
	  
	  logpath ='/home/ec2-user/espb/AWS/ESRally/logs/'
          shutil.make_archive(logpath + test['name']+'-log', 'zip', logpath)
	  boto3.resource('s3').meta.client.upload_file(logpath+ test['name']+'-log.zip', args.bucket, test['name']+'-log.zip')

  print('Script is done!')

  # tear down stack and benchmarking
  #boto3.client('cloudformation').delete_stack(stackName='ES-Benchmarking-Stack')
