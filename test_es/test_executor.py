import argparse
import os
import sys
import threading
import json
import collections
import requests
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
    parser.add_argument('--instance_type', help='Instance Type', default="m3.medium")
    parser.add_argument('--region', help='AWS region.', default='us-west-2')
    parser.add_argument('--data_file', help='If set, script will read that file to create instances.', required=True)
    parser.add_argument('--save_instance_on_failure', help='If set, script will not terminate the instance on failure.', action='store_true')
    parser.add_argument('--debug', help='Verbosity in output.', action='store_true')
    args = parser.parse_args()

    # Verify you are running on ec2 vs laptop:
    bRunningOnEC2 = False
    try:
        r = requests.head('http://169.254.169.254/latest/meta-data/', timeout=1.5)
        if r.status_code == 200:
            bRunningOnEC2 = True
    except:
        pass
    if bRunningOnEC2 is False:
        if 'AWS_ACCESS_KEY_ID' not in os.environ or 'AWS_SECRET_ACCESS_KEY' not in os.environ:
            print('You are not running on an EC2 instance and you do not have AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as env vars.')

    if not os.path.exists(args.data_file):
        print('***Error: File does not exist: {}'.format(args.data_file))
        sys.exit(1)

    if os.path.abspath(args.data_file) == os.path.abspath(os.path.join(os.path.dirname(__file__), 'data_file.json')):
        print('***WARNING: Using supplied data_file.json.  It is highly recommended to use your own.')

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
    version = '1.0.5'
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
            # command line are trumps what is in data_file.json:
            if args.save_instance_on_failure is True:
                test['save_on_failure'] = args.save_instance_on_failure
            elif 'save_on_failure' in test:
                test['save_on_failure'] = test['save_on_failure']
            else:
                # For legacy purposes, lets set it to false:
                test['save_on_failure'] = False
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
