import os
from os import listdir
from os.path import isfile, join
import sys
import time
import argparse
import json
import boto3
import docker
import zipfile

rootpath = '/home/ec2-user/espb/AWS/'

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


def init_esrally():
  client = docker.from_env()
  container = client.containers.get('esrally')

  cmd = 'mkdir /home/es/.rally'
  container.exec_run(cmd, tty=True, privileged=False, user='root')

  cmd = 'chown -R es:es /home/es/.rally'
  container.exec_run(cmd, tty=True, privileged=False, user='root')
  return


def run_single_test(test, bucket):

  client = docker.from_env()
  container = client.containers.get('esrally')

  cmd = 'mkdir /home/es/.rally'
  container.exec_run(cmd, tty=True, privileged=False, user='root')
  
  #cmd = 'docker cp {0} esrally:/home/es/.rally/rally.ini'.format(test['rally_config'])
  container.put_archive('/home/es/.rally/rally.ini', test['rally_config'])

  cmd = 'chown es:es /home/es/.rally/rally.ini'
  container.exec_run(cmd, tty=True, privileged=False, user='root')

  cmd= "test['test']"
  container.exec_run(cmd, tty=True, privileged=False, user='root')

  cmd = 'chmod -R 775 /home/es/.rally/logs'
  container.exec_run(cmd, tty=True, privileged=False, user='root')
  
  #cmd = 'docker cp esrally:/home/es/.rally/logs/. /home/ec2-user/espb/AWS/ESRally/logs'
  container.get_archive('/home/es/.rally/logs/.')

  return


if __name__ == '__main__':
    
  args = parseArgs()
  boto3.resource('s3').meta.client.download_file(args.bucket, 'data_file.json', 'data_file.json')
  with open('data_file.json') as json_data:
    data = json.load(json_data)

  client = docker.from_env()
  for i in range(0,10):
    if len(client.containers.list()) < 3:
      time.sleep(30)
    else:
      time.sleep(30)
      break

  init_esrally()

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
          for subdir, dirs, files in os.walk(logpath):
            for file in files:
              boto3.resource('s3').meta.client.upload_file(logpath+file, args.bucket, file)

  print('Script is done!')

  # tear down stack and benchmarking
  #boto3.client('cloudformation').delete_stack(stackName='ES-Benchmarking-Stack')
