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
    
  args = parseArgs()
  data = boto3.resource('s3').meta.client.download_file(args.bucket, 'data_fileljson', '/home/ec2-user/espb/AWS/ESRally/data_file.json')

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
          threads.append(threading.Thread(target=run_single_test, kwargs=test))
      # Start running the threads:
      print('starting threads...')
      for t in threads:
          t.start()
      # Wait for all threads to stop:
      print('waiting for threads...')
      for t in threads:
          t.join()
  print('Script is done!')