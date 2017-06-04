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
  bashCommand = 'docker exec -it -u root esrally mkdir /home/es/.rally'
  run(bashCommand)

  bashCommand = 'docker exec -it -u root esrally chown -R es:es /home/es/.rally'
  run(bashCommand)
  return


def run_single_test(test, bucket):

  bashCommand = 'docker cp {0} esrally:/home/es/.rally/rally.ini'.format(test['rally_config'])
  run(bashCommand)

  bashCommand = 'docker exec -it esrally -u root chown es:es /home/es/.rally/rally.ini'
  run(bashCommand)

  bashCommand = 'docker exec -it esrally {0}'.format(test['test'])
  print bashCommand
  run(bashCommand)
  
  #bashCommand = 'docker cp esrally:/home/es/.rally/logs/ /home/ec2-user/espb/AWS/ESRally'
  #run(bashCommand)

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

    if returncode != 0 and raiseOnFailure is True:
        print '***Error in command and raiseOnFailure is True so exiting. CMD:\n{0}'.format(cmd)
        all_output = output

        print 'This is the output from that command, if any:\n{0}'.format(all_output)
        #raise Exception('Command_Error')

    return output, returncode


if __name__ == '__main__':
    
  args = parseArgs()
  boto3.resource('s3').meta.client.download_file(args.bucket, 'data_file.json', 'data_file.json')
  with open('data_file.json') as json_data:
    data = json.load(json_data)

  #init_esrally()

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
	  
	  logpath ='logs'
    with ZipFile(logpath + test['name']+'-log', 'w') as myzip:
      myzip.write(logpath)
    '''
          shutil.make_archive(logpath + test['name']+'-log', 'zip', logpath)
	  boto3.resource('s3').meta.client.upload_file(logpath+ test['name']+'-log.zip', args.bucket, test['name']+'-log.zip')
    '''
  print('Script is done!')

  # tear down stack and benchmarking
  #boto3.client('cloudformation').delete_stack(stackName='ES-Benchmarking-Stack')
