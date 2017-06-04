import os
from os import listdir
from os.path import isfile, join
import sys
import time, datetime
import argparse
import json
import boto3
import docker
import zipfile
import subprocess
import logging

LOG_FILENAME = 'logging.out'
logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO)


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


def run_single_test(test, bucket):
  try:
    bashCommand = 'docker cp {0} esrally:/home/es/.rally/rally.ini'.format(test['rally_config'])
    run(bashCommand)

    bashCommand = 'docker exec -it -u root esrally chown es:es /home/es/.rally/rally.ini'
    run(bashCommand)

    bashCommand = 'docker exec -it esrally {0}'.format(test['test'])
    print bashCommand
    run(bashCommand)

    bashCommand = 'docker exec -it -u root esrally chmod -R 775 /home/es/.rally/logs'
    run(bashCommand)
    
    bashCommand = 'docker cp esrally:/home/es/.rally/logs/. /home/ec2-user/espb/AWS/ESRally/logs'
    run(bashCommand)
  except Exception as e:
    logging.info(datetime.datetime.now())
    logging.exception(str(e))
  return

# General purpose run command:
def run(cmd, raiseOnFailure=True, retry_count=0, retry_sleep_secs=30):
    try:
        xrange
    except NameError:
        xrange = range
    for i_attempt in xrange(retry_count + 1):
        output = None
        stdout = None
        stderr = None
        returncode = None
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
            output = p.communicate()[0]
            print output
            returncode = p.returncode
        except Exception:
            print 'Error printing '
        if returncode != 0:
            # There was an error, lets retry, if possible:
            if i_attempt != retry_count:
                # Only sleep if not end of the loop:
                print 'Retrying'
                time.sleep(retry_sleep_secs)
            continue
        else:
            # Command was success, let's not retry:
            break

def check_container_exists(name):
  try:
    client = docker.DockerClient(version='1.24')
    for i in range(0,5):
      if client.containers.get(name).name != name:
        time.sleep(30)
      else:
        break
  except Exception as e:
    logging.info(str(datetime.datetime.now())+": container {} not found".format(name))
    logging.exception(str(e))
    sys.exit(1)
  return

if __name__ == '__main__':
  logging.info(str(datetime.datetime.now()) + ': starting test')
  args = parseArgs()
  boto3.resource('s3').meta.client.download_file(args.bucket, 'data_file.json', 'data_file.json')
  with open('data_file.json') as json_data:
    data = json.load(json_data)
  logging.info(str(datetime.datetime.now()) + ': waiting for containers to initalize') 

  client = docker.DockerClient(version='1.24')

  for i in range(0,10):
    if len(client.containers.list()) < 3:
      logging.info(str(datetime.datetime.now()) + ': Still waiting for containers to initalize') 
      time.sleep(30)
    else:
      # Make sure all containers exist and are up and running
      check_container_exists('kibana')
      check_container_exists('elasticsearch')
      check_container_exists('esrally')
      time.sleep(300)
      logging.info(str(datetime.datetime.now()) + ': Containers initialized') 
      break

  # Run all tests of a test suite in parallel:
  for test_suite, tests in data['test_suites'].items():
      print('Running test suite: {}'.format(test_suite))
      threads = []
      for test in tests:
          if 'do_run' in test and not test['do_run']:
              print("Skipping: {} in {} because do_run is set to false.".format(test['name'], test_suite))
              continue
          test['test_suite_name'] = test_suite
          logging.info(str(datetime.datetime.now()) + ': running test: {0}'.format(test['name']))
          run_single_test(test, args.bucket)

          try: 
            logpath ='/home/ec2-user/espb/AWS/ESRally/logs/'
            for subdir, dirs, files in os.walk(logpath):
              for file in files:
                boto3.resource('s3').meta.client.upload_file(logpath+file, args.bucket, file)
          except Exception as e:
            logging.info(str(datetime.datetime.now()) + ': error updating logs')
            logging.exception(str(e))
  logging.info(str(datetime.datetime.now()) + ': script finished')
  print('Script is done!')
  
  # tear down stack and benchmarking
  #boto3.client('cloudformation').delete_stack(stackName='ES-Benchmarking-Stack')
