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
import urllib2, requests
import base64
import subprocess
import logging

LOG_FILENAME = '/home/ec2-user/espb/AWS/logging.out'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)


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
    logging.info('copying rally config')
    bashCommand = 'docker cp {0} esrally:/home/es/.rally/rally.ini'.format(test['rally_config'])
    run(bashCommand, retry_count=5)

    logging.info('changing rally.ini owner')
    bashCommand = 'docker exec -i -u root esrally chown es:es /home/es/.rally/rally.ini'
    run(bashCommand, retry_count=5)

    bashCommand = 'docker exec -i esrally {0}'.format(test['test'])
    logging.info('running test command {}'.format(test['test']))
    print bashCommand
    run(bashCommand, retry_count=5)

    logging.info('changing rally log owner')
    bashCommand = 'docker exec -i -u root esrally chmod -R 775 /home/es/.rally/logs'
    run(bashCommand, retry_count=5)
    
    logging.info('copying logs')
    bashCommand = 'docker cp esrally:/home/es/.rally/logs/. /home/ec2-user/espb/AWS/ESRally/logs'
    run(bashCommand, retry_count=5)
  except Exception as e:
    logging.info(datetime.datetime.now())
    logging.exception(str(e))
  return

'''
  General purpose run command. Taken and modified slightly from original ES_Test.py
  Runs bash commands via Python. Tried using the Python Docker API, but was having client/server
  version issues and could not get the API to work properly. May need to be re-explored in the future.
'''
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
            logging.info(output)
            logging.info(p.returncode)
            returncode = p.returncode

        except Exception:
            print 'Error printing '
            logging.info('Error printing')
        if returncode != 0:
            # There was an error, lets retry, if possible:
            if i_attempt != retry_count:
                # Only sleep if not end of the loop:
                logging.info('Retrying')
                time.sleep(retry_sleep_secs)
            else:
              logging.info('too many tries')
            continue
        else:
            # Command was success, let's not retry:
            break
 
'''
  Make sure a container exists and can be referenced by name. 
  It can take several minutes for the images to build and the 
  container services to be completely up and running
'''
def check_container_exists(name):
  try:
    client = docker.DockerClient(version='1.24')
    for i in range(0,5):
      if client.containers.get(name).name != name:
        logging.info('Still waiting on ' + name)
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
  curr_date = datetime.datetime.now()
  args = parseArgs()
  boto3.resource('s3').meta.client.download_file(args.bucket, 'data_file.json', 'data_file.json')
  with open('data_file.json') as json_data:
    data = json.load(json_data)
  logging.info(str(datetime.datetime.now()) + ': waiting for containers to initalize') 

  client = docker.DockerClient(version='1.24')

  # Make sure all containers exist and are up and running
  # It takes time for Docker images and container services to be up and running
  for i in range(0,10):
    if len(client.containers.list()) < 3:
      logging.info(str(datetime.datetime.now()) + ': Still waiting for containers to initalize') 
      time.sleep(30)
    else:
      check_container_exists('kibana')
      check_container_exists('elasticsearch')
      check_container_exists('esrally')
      logging.info(str(datetime.datetime.now()) + ': Containers initialized') 
      break

  # Run test suites. Still linear run -need to explore threading and parallel running of tests
  for test_suite, tests in data['test_suites'].items():
      print('Running test suite: {}'.format(test_suite))
      threads = []
      # Run a single test
      for test in tests:
        if 'do_run' in test and not test['do_run']:
            print("Skipping: {} in {} because do_run is set to false.".format(test['name'], test_suite))
            continue
        test['test_suite_name'] = test_suite
        logging.info(str(datetime.datetime.now()) + ': running test: {0}'.format(test['name']))
        run_single_test(test, args.bucket)

        logpath ='/home/ec2-user/espb/AWS/ESRally/logs/'
        # Get esrally logs and save to S3
        # right now just dumping to S3 bucket. Will need to add better organization
        try: 
          for subdir, dirs, files in os.walk(logpath):
            for file in files:
              boto3.resource('s3').meta.client.upload_file(logpath+file, args.bucket, file)
        except Exception as e:
          logging.info(str(datetime.datetime.now()) + ': error saving rally logs')
          logging.exception(str(e))

        #Get monitoring metrics and save to S3
        #curl -u elastic -XGET '172.25.0.2:9200/rally-2017/metrics/_search?q=environment:benchmark'
        try:
          username = 'elastic'
          password = 'changeme'
          year = curr_date.year
          month = curr_date.strftime('%m')
          url = 'http://172.25.0.3:9200/rally-metrics-{0}-{1}/metrics/_search?q=environment:benchmark'.format(year, month)
          request = urllib2.Request(url)
          base64string = base64.b64encode('%s:%s' % (username, password))
          request.add_header("Authorization", "Basic %s" % base64string)   
          result = urllib2.urlopen(request)
          f = open(logpath+'metrics_store.json', 'w')
          f.write(result.read())
          f.close()
          boto3.resource('s3').meta.client.upload_file(logpath+'metrics_store.json', args.bucket, 'metrics_store.json')
        except Exception as e:
          logging.info(str(datetime.datetime.now()) + ': error saving metrics store')
          logging.exception(str(e))
  logging.info(str(datetime.datetime.now()) + ': script finished')
  print('Script is done!')
  
  # tear down stack and benchmarking
  region_resp=requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document')
  region = str(json.loads(region_resp.text)['region'])
  boto3.client('cloudformation', region_name=region).delete_stack(StackName='ES-Benchmarking-Stack')
