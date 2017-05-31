import os
import sys
import threading
import argparse
import json
import collections
import requests
import boto3
import re
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
  parser.add_argument('--bucket', help='If set, script will read that file to create instances.', required=True)
  return parser.parse_args()


def run_single_test(test, bucket):
  test_params=json.loads(single_test)
  output, returncode = run('docker exec -it esrally {0}'.format(test_params['test']), debug=self.debug)
  if returncode:
    response = boto3.resource('s3').meta.client.upload_file('logging', bucket, 'log.txt')
  return

# General purpose run command:
def run(cmd, hide_command=True, raiseOnFailure=True,
        retry_count=0,
        retry_sleep_secs=30, debug=False):
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
        output = safe_str(p.communicate()[0])
        returncode = p.returncode
    except Exception as e:
      logging.exception(str(e))
    if returncode != 0:
        # There was an error, lets retry, if possible:
        if i_attempt != retry_count:
            # Only sleep if not end of the loop:
            logging.exception('retrying command: {}, after sleeping: {}s'.format(cmd, retry_sleep_secs))
            time.sleep(retry_sleep_secs)
        continue
    else:
        # Command was success, let's not retry:
        break

  if returncode != 0 and raiseOnFailure is True:
    logging.exception('***Error in command and raiseOnFailure is True so exiting. CMD:\n{0}'.format(cmd))
    all_output = output

    logging.exception('This is the output from that command, if any:\n{0}'.format(all_output))
    raise Exception('Command_Error')

  if debug is True:
    logging.exception('Debug Information:\noutput:\n{0}\nreturncode: {1}'.format(output, returncode))
  return output, returncode

  def safe_str(obj):
        """ return the byte string representation of obj """
        try:
            return str(obj)
        except UnicodeEncodeError:
            # obj is unicode
            return unicode(obj).encode('unicode_escape')

  # Setup thread safe logging:
  def setup_logging(self):
      self.log = logging.getLogger(self.name)
      self.log.setLevel(logging.DEBUG)

      # Create the Formater:
      logFormatter = logging.Formatter("%(asctime)s %(message)s")
      logFormatter.converter = time.gmtime

      # Write to individual file:
      fileHandler = logging.FileHandler(self.log_name)
      fileHandler.setFormatter(logFormatter)
      self.log.addHandler(fileHandler)

      # And write to console output:
      consoleHandler = logging.StreamHandler()
      consoleHandler.setFormatter(logFormatter)
      self.log.addHandler(consoleHandler)


if __name__ == '__main__':
    
  args = parseArgs()
  data = boto3.resource('s3').meta.client.download_file(args.bucket, 'data_file.json', '/home/ec2-user/espb/AWS/ESRally/data_file.json')

  # Run all tests of a test suite in parallel:
  for test_suite, tests in data['test_suites'].items():
      print('Running test suite: {}'.format(test_suite))
      threads = []
      for test in tests:
          if 'do_run' in test and test['do_run'] is not True:
              print("Skipping: {} in {} because do_run is set to false in {}.".format(test['name'], test_suite, args.data_file))
              continue
          test['test_suite_name'] = test_suite
          test['debug'] = args.debug
          threads.append(threading.Thread(target=run_single_test, kwargs=[test, args.bucket]))
      # Start running the threads:
      print('starting threads...')
      for t in threads:
          t.start()
      # Wait for all threads to stop:
      print('waiting for threads...')
      for t in threads:
          t.join()
  print('Script is done!')

  # tear down stack and benchmarking
  boto3.client('cloudformation').delete_stack(stackName='ES-Benchmarking-Stack')