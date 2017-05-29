import datetime
import uuid
import os
import sys
import time
import traceback
import logging
import logging.handlers
import subprocess
import json
import tempfile

try:
    input = raw_input
except NameError:
    pass

# Vanilla linux ami from AWS:
# https://aws.amazon.com/amazon-linux-ami/
ami = {
    'us-east-1': 'ami-c481fad3',
    'us-east-2': 'ami-71ca9114',
    'us-west-2': 'ami-b04e92d0',
    'us-west-1': 'ami-de347abe'
}

# Custom exception when creating an instance:
class CreateInstanceException(Exception):
    def __init__(self, message, instance_id=None):

        # Call the base class constructor with the parameters it needs
        super(CreateInstanceException, self).__init__(message)

        # Now for your custom code...
        self.instance_id = instance_id

# Class that tests elasticsearch on an aws instance:
class ES_Test():

    # Class Constructor:
    def __init__(self, region, instance_type, test_suite_name='basic_suite', name='test', ssh_user='ec2-user',
                 tag_name='tester', tag_role='tester', tag_env='test', tag_owner='alex',
                 test='esrally --pipeline=from-distribution --distribution-version=5.0.0 --quiet',
                 test_options='--report-format csv --report-file /home/ec2-user/rally_report.csv',
                 subnet_id=None, security_group_ids=None, instance_profile=None, root_size_gb=12,
                 rally_config=None, save_on_failure=False, debug=False):
        # input variables:
        self.test_suite_name = test_suite_name
        self.name = name
        self.region = region
        self.instance_type = instance_type
        self.ssh_user=ssh_user
        self.subnet_id=subnet_id
        self.security_group_ids=security_group_ids
        self.instance_profile=instance_profile
        self.tag_name = tag_name
        self.tag_role = tag_role
        self.tag_env = tag_env
        self.tag_owner = tag_owner
        self.test = test
        self.test_options = test_options
        self.root_size_gb = root_size_gb
        self.rally_config = rally_config
        self.save_on_failure = save_on_failure
        self.debug = debug

        # class variables:
        self.log = None
        self.block_devices_path_file_name = None
        self.output_dir = os.path.join('test_results',
                                       '{}-rally'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')),
                                       self.test_suite_name,
                                       self.name)
        self.log_name = os.path.join(self.output_dir, '{}.log'.format(self.name))
        self.ami_id = ami[self.region]
        self.start_time = datetime.datetime.now()
        self.bIsRunning = True
        self.key_name = 'ami-test-' + str(uuid.uuid4())
        self.instance = None
        self.instance_id = None
        self.ip = None
        self.generated_id_rsa = 'ec2-generated-id_rsa-{}'.format(self.name)
        self.ssh_opts = '-o ControlMaster=no -o ConnectTimeout=30 -t -n -o PreferredAuthentications=publickey -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
        self.scp_opts = '-o ControlMaster=no -o ConnectTimeout=30       -o PreferredAuthentications=publickey -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes'

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # set up logging:
        self.setup_logging()
        # create the instance and install everything:
        self.setup_test()

    # Good way to see how long this object has been alive:
    def get_current_elapsed_time_in_seconds(self):
        diff = datetime.datetime.now() - self.start_time
        return diff.seconds

    # Create instance and any resources needed:
    def setup_test(self):
        self.createKeyPair()
        self.launch_instance()
        self.wait_for_instance_to_come_up()
        self.wait_for_ssh()
        self.copy_install_scripts()
        self.run_install_scripts()

    # Run the test script:
    def run_tests(self):
        self.say('Running tests... This can take many hours to run...', banner='*')
        # Generate a temp shell script to run the tests:
        os_fd, full_path_file_name = tempfile.mkstemp(prefix='test_esrally_', suffix='.sh', text=True)
        file_name = os.path.basename(full_path_file_name)
        os.close(os_fd)
        with open(full_path_file_name, 'w') as fd:
            fd.write('{} {}  2>&1 | tee -a /home/ec2-user/es_rally_output.txt\n'.format(self.test, self.test_options))

        # Copy the test script over:
        self.say('=========================SCP\'ing Test Scripts to remote machine...')
        cmd = 'scp -i {} {} {} ec2-user@{}:/home/ec2-user/'.format(self.generated_id_rsa, self.scp_opts, full_path_file_name, self.ip)
        output, returncode = self.run(cmd, debug=self.debug)
        self.say(output)

        # Now run the test script:
        cmd = 'ssh -i {} {} ec2-user@{} "screen -d -m bash /home/ec2-user/{}"'.format(self.generated_id_rsa,
                                                                                        self.ssh_opts,
                                                                                        self.ip,
                                                                                        file_name)
        output, returncode = self.run(cmd, debug=self.debug)
        # Now wait for the script to finish:
        while True:
            self.say('Waiting for test to finish...')

            # Exit run if disk space is full:
            if self.is_disk_full() is True:
                break

            # Print system stats:
            self.print_instance_stats()

            # Check to see if catastrophic error:
            if self.is_catastrophic_error():
                break

            # Check if esrally is running:
            if not self.is_esrally_running():
                break

            time.sleep(60)

        # We're done. Success or failure.
        # Collect the csv, if any:
        self.collect_artifacts()
        self.say('Test is done!')

    def collect_artifacts(self):
        if self.remote_file_exists('/home/ec2-user/rally_report.csv'):
            self.say('Collecting /home/ec2-user/rally_report.csv from test...')
            cmd = 'scp -i {} {} ec2-user@{}:/home/ec2-user/rally_report.csv {}'.format(self.generated_id_rsa,
                                                                             self.scp_opts,
                                                                             self.ip,
                                                                             self.output_dir)
            output, returncode = self.run(cmd, debug=self.debug)
            self.say('File has been saved here: {}'.format(os.path.join(self.output_dir, 'rally_report.csv')))
        if self.remote_file_exists('/home/ec2-user/es_rally_output.txt'):
            self.say('Collecting /home/ec2-user/es_rally_output.txt from test...')
            cmd = 'scp -i {} {} ec2-user@{}:/home/ec2-user/es_rally_output.txt {}'.format(self.generated_id_rsa,
                                                                             self.scp_opts,
                                                                             self.ip,
                                                                             self.output_dir)
            output, returncode = self.run(cmd, debug=self.debug)
            self.say('File has been saved here: {}'.format(os.path.join(self.output_dir, 'es_rally_output.txt')))

    def is_catastrophic_error(self):
        if self.remote_file_exists('/home/ec2-user/es_rally_output.txt'):
            cmd = 'ssh -i {} {} ec2-user@{} cat /home/ec2-user/es_rally_output.txt'.format(self.generated_id_rsa,
                                                                                           self.ssh_opts,
                                                                                           self.ip)
            output, returncode = self.run(cmd, raiseOnFailure=False, debug=self.debug)
            if 'ERROR: Cannot race' in output or 'FAILURE' in output:
                self.say('***Error running rally.  Here is the contents of /home/ec2-user/es_rally_output.txt')
                self.say('-' * 50)
                self.say(output)
                self.say('-' * 50)
                return True
        return False

    def is_esrally_running(self):
        cmd = 'ssh -i {} {} ec2-user@{} {}'.format(self.generated_id_rsa,
                                                   self.ssh_opts,
                                                   self.ip,
                                                   'bash /home/ec2-user/install_scripts/is_rally_running.sh')
        output, returncode = self.run(cmd, raiseOnFailure=False, debug=self.debug)
        self.say(output)
        if 'Stopped' in output:
            self.say('esrally has stopped running. Exiting.')
            return False
        else:
            self.say('esrally is still running. output of esrally is on the remote machine here: /home/ec2-user/es_rally_output.txt')
            return True

        if self.debug is True:
            self.say('DEBUG: current output of /home/ec2-user/es_rally_output.txt: \n{}\n{}'.format(output, '-' * 50))

    def remote_file_exists(self, remote_file):
        cmd = 'ssh -i {} {} ec2-user@{} test -f "{}" && echo file_found || echo file_not_found'.format(self.generated_id_rsa,
                                                                                                       self.ssh_opts,
                                                                                                       self.ip,
                                                                                                       remote_file)

        output, returncode = self.run(cmd, debug=self.debug)
        if "file_found" in output:
            return True
        else:
            return False

    def is_disk_full(self):
        cmd = 'ssh -i {} {} ec2-user@{} df --total -hl'.format(self.generated_id_rsa,
                                                               self.ssh_opts,
                                                               self.ip)
        output, returncode = self.run(cmd, debug=self.debug)
        disk_space_full = False
        for line in output.split('\n'):
            if line.strip() == '':
                continue
            if len(line.split()) >= 4:
                percent = line.split()[4]
                filesystem = line.split()[0]
                mountedon = line.split()[5]
                if filesystem == 'total':
                    continue
                try:
                    if int(percent.replace('%', '')) >= 100:
                        self.say('***ERROR: Disk usage is at 100%: {}:{}'.format(filesystem, percent))
                        disk_space_full = True
                    elif int(percent.replace('%', '')) > 90:
                        self.say('***WARNING: Disk usage is above 90%: {}:{}'.format(filesystem, percent))
                    self.say('Disk Usage on FileSystem: {}, mounted at: {} is at {} used disk space.'.format(filesystem.ljust(12), mountedon.ljust(8), percent))
                except:
                    pass

        return disk_space_full

    def print_instance_stats(self):
        cmd = 'ssh -i {} -t {} ec2-user@{} top -n 1 | grep Cpu'.format(self.generated_id_rsa,
                                                                       self.ssh_opts,
                                                                       self.ip)
        output, returncode = self.run(cmd, debug=self.debug)
        for line in output.split('\n'):
            line = line.strip()
            if 'Cpu' in line:
                self.say('{}'.format(line))
                break

    # Tear down instance and any resources:
    def tear_down_test(self):
        self.say('Test is done...', banner='*')
        if self.save_on_failure is True:
            self.say('Not tearing down instance since save_on_failure is True.')
            self.say('To ssh onto instance, use this command: ssh ec2-user@{} -i {}'.format(self.ip, self.generated_id_rsa))
        else:
            self.say('Destroying Instance...')
            try:
                self.deleteKeyPair()
                if self.block_devices_path_file_name is not None:
                    if os.path.exists(self.block_devices_path_file_name):
                        os.remove(self.block_devices_path_file_name)
                if os.path.exists(self.generated_id_rsa):
                    os.remove(self.generated_id_rsa)
                self.terminateInstance()
            except:
                self.say(traceback.format_exc())

        if self.bIsRunning is True:
            self.bIsRunning = False
            diff = datetime.datetime.now() - self.start_time
            elapsed_time = datetime.timedelta(seconds=diff.seconds)
            self.say(self.name + ' :Elapsed Time: ' + str(elapsed_time))
            return elapsed_time

    # General purpose function to create an instance:
    def launch_instance(self):
        self.say('Creating Instance in region: {0}'.format(self.region), banner="*")
        # If you don't specify a security group when launching an instance,
        # Amazon EC2 uses the default security group.
        sg = '' if self.security_group_ids is None else ' --security-group-ids ' + self.security_group_ids

        # [EC2-VPC only accounts] If you don't specify a subnet in the request,
        # we choose a default subnet from your default VPC for you.
        sn = '' if self.subnet_id is None else ' --subnet-id ' + self.subnet_id

        # Instance Profile of instance:
        ip = '' if self.instance_profile is None else '' + self.instance_profile

        # Describe the image, so that we can increase the root block device:
        cmd = 'aws ec2 describe-images --image-ids {} --region {}'.format(self.ami_id, self.region)
        output, returncode = self.run(cmd, retry_count=2, debug=self.debug)
        j = json.loads(output)
        block_devices = j['Images'][0]['BlockDeviceMappings']
        for bd in block_devices:
            if 'Ebs' in bd:
                self.say('Existing volume size: {} (tweaking to {})'.format(bd['Ebs']['VolumeSize'], self.root_size_gb))
                bd['Ebs']['VolumeSize'] = self.root_size_gb
                del bd['Ebs']['Encrypted']

        # This is for VPC only, not EC2 Classic:
        os_fd, self.block_devices_path_file_name = tempfile.mkstemp(prefix='test_esrally_', suffix='.json', text=True)
        os.close(os_fd)
        with open(self.block_devices_path_file_name, 'w') as fp:
            json.dump(block_devices, fp)
        cmd = 'aws ec2 run-instances --region ' + self.region + \
              ' --image-id ' + self.ami_id + \
              ' --key-name ' + self.key_name + \
              ' --placement Tenancy=default' + \
              ' --instance-type ' + self.instance_type + \
              ' --block-device-mappings file://{}'.format(self.block_devices_path_file_name) + \
              sn + \
              sg + \
              ip

        output, returncode = self.run(cmd, retry_count=2, debug=self.debug)
        self.instance_id = json.loads(output)['Instances'][0]['InstanceId']
        self.say('Instance is being created: ' + self.instance_id)

        self.say('Adding tags to instance...')
        tags_dict = {'role': self.tag_role, 'owner': self.tag_owner,
        'Name': self.tag_name, 'environment': self.tag_env}
        tags_option = ''
        tags_option = ' --tags'
        for k, v in tags_dict.items():
            tags_option += ' Key={0},Value={1}'.format(k, v)

        # Add Tags to instance
        cmd = 'aws ec2 create-tags --region ' + self.region + \
              ' --resources ' + str(self.instance_id) + tags_option
        output, returncode = self.run(cmd, retry_count=3, debug=self.debug)

    # Wait for instance to come up:
    def wait_for_instance_to_come_up(self):
        # Wait up to 5 min for instance to be ready:
        cmd = 'aws ec2 describe-instance-status --region ' + self.region + \
              ' --instance-ids ' + str(self.instance_id)
        bInstanceReady = False
        loop_counter = 35
        sleep_time = 15
        self.say('Waiting for instance to be ready...')
        for i in range(loop_counter):
            output, returncode = self.run(cmd, retry_count=3, debug=self.debug)
            j = json.loads(output)
            if len(j['InstanceStatuses']) == 0:
                current_state = 'UNKNOWN'
                current_system_status = 'UNKNOWN'
                current_instance_status = 'UNKNOWN'
            else:
                current_state = str(j['InstanceStatuses'][0]['InstanceState']['Name'])
                current_system_status = str(j['InstanceStatuses'][0]['SystemStatus']['Status'])
                current_instance_status = str(j['InstanceStatuses'][0]['InstanceStatus']['Status'])
            if current_state == 'running' and current_system_status == 'ok' and current_instance_status == 'ok':
                self.say('Instance is running and status is good!')
                bInstanceReady = True
                break
            else:
                self.say('Instance is not ready. Current Status: {}. Attempt {}/{}'.format(current_instance_status, i, loop_counter))
            time.sleep(sleep_time)
        if bInstanceReady is False:
            self.say('***Error: We waited {0} seconds for instance to be ready and its not.'.format(loop_counter * sleep_time))
            raise CreateInstanceException("Instance_Not_Started", instance_id=str(self.instance_id))

    # Wait for the instance to be ssh-able
    def wait_for_ssh(self):
        # Wait for ssh. First get the IP address:
        cmd = 'aws ec2 describe-instances --region ' + self.region +\
              ' --instance-ids ' + str(self.instance_id)
        output, returncode = self.run(cmd, retry_count=3, debug=self.debug)
        # Now that the instance is up and runing get the public and/or private ip:
        instance = json.loads(output)['Reservations'][0]['Instances'][0]
        ip_addresses = []
        if 'PrivateIpAddress' in instance:
            ip_addresses.append(instance['PrivateIpAddress'])
        if 'PublicIpAddress' in instance:
            ip_addresses.append(instance['PublicIpAddress'])

        ssh_cmd = 'ssh -i {0} {1}'.format(self.generated_id_rsa, self.ssh_opts)

        loop_counter = 30
        bInstanceSshReady = False
        self.say('Waiting for ssh to work...')
        for i in range(loop_counter):
            for ip in ip_addresses:
                cmd = '{0} {1}@{2} \'echo hello world\''.format(ssh_cmd, self.ssh_user, ip)
                output, returncode = self.run(cmd, raiseOnFailure=False, debug=self.debug)
                if returncode == 0:
                    bInstanceSshReady = True
                    self.ip = ip
                    break
            if bInstanceSshReady is True:
                break
            else:
                self.say('Instance is not ssh-able... retrying...')
                time.sleep(10)

        if bInstanceSshReady is False:
            self.say('***Error: We waited 5 min for instance to be ssh-able and its not.')
            raise CreateInstanceException("Instance_not_ssh_able", instance_id=str(self.instance_id))

        self.say('Instance is ready and sshable with ip: {}'.format(self.ip))

    # Copy install scripts to target machine:
    def copy_install_scripts(self):
        self.say('Copying install_scripts dir to /home/ec2-user/ ...: {}'.format(self.ip), banner='*')
        cmd = 'scp -i {} {} -r install_scripts ec2-user@{}:/home/ec2-user/'.format(self.generated_id_rsa, self.scp_opts, self.ip)
        output, returncode = self.run(cmd, debug=self.debug)

        self.say('Copying the rally.ini to /home/ec2-user/.rally/rally.ini : {}'.format(self.ip))
        cmd = 'ssh -i {} {} ec2-user@{} mkdir /home/ec2-user/.rally/ '.format(self.generated_id_rsa, self.ssh_opts, self.ip)
        output, returncode = self.run(cmd, debug=self.debug)
        cmd = 'scp -i {} {} {} ec2-user@{}:/home/ec2-user/.rally/rally.ini'.format(self.generated_id_rsa, self.scp_opts, self.rally_config ,self.ip)
        output, returncode = self.run(cmd, debug=self.debug)

    # Run the install script:
    def run_install_scripts(self):
        self.say('Running install script on: {}'.format(self.ip), banner='*')
        cmd = 'ssh -i {} {} ec2-user@{} "bash /home/ec2-user/install_scripts/install.sh"'.format(self.generated_id_rsa, self.ssh_opts, self.ip)
        output, returncode = self.run(cmd, debug=self.debug)
        if 'All done!' not in output:
            self.say('***Error running install.sh.  Here is the output:\n{}'.format(output))
            raise CreateInstanceException("run_install_scripts on {}".format(self.ip), instance_id=str(self.instance_id))
        else:
            self.say('Successfully ran install.sh!')
        self.say('Tweaking OS variables...')
        cmd = 'ssh -i {} {} ec2-user@{} "sudo bash /home/ec2-user/install_scripts/root_install_commands.sh"'.format(self.generated_id_rsa, self.ssh_opts, self.ip)
        output, returncode = self.run(cmd, debug=self.debug)
        self.say(output)
        if 'All done!' not in output:
            self.say('***Error running root_install_commands.sh.  Here is the output:\n{}'.format(output))
            raise CreateInstanceException("run_install_scripts on {}".format(self.ip), instance_id=str(self.instance_id))
        else:
            self.say('Successfully ran root_install_commands.sh!')
        self.say('rebooting the machine for settings to take place...')
        cmd = 'ssh -i {} {} ec2-user@{} "sudo reboot"'.format(self.generated_id_rsa, self.ssh_opts, self.ip)
        output, returncode = self.run(cmd, debug=self.debug)
        self.wait_for_ssh()

    # Delete a key pair:
    def deleteKeyPair(self):
        self.say('Deleting key name: {0}'.format(self.key_name))
        cmd = 'aws ec2 delete-key-pair --region {0} --key-name {1}'.format(self.region, self.key_name)
        output, returncode = self.run(cmd, retry_count=3, debug=self.debug)

    # Create a key pair:
    def createKeyPair(self):
        self.say('Creating temporary key pair:{0} output_id_rsa: {1}'.format(self.key_name, self.generated_id_rsa))
        cmd = 'aws ec2 create-key-pair --key-name {0} --region {1}'.format(self.key_name, self.region)
        output, returncode = self.run(cmd, retry_count=3, debug=self.debug)
        j = json.loads(output)
        with open(self.generated_id_rsa, 'w') as fd:
            fd.write(j['KeyMaterial'])
        os.chmod(self.generated_id_rsa, 0o600)

    # Terminate Instance:
    def terminateInstance(self):
        self.say('Terminating instance: {0}'.format(self.instance_id))
        if self.instance_id is not None:
            cmd = 'aws ec2 terminate-instances --region {0} --instance-ids {1}'.format(self.region, self.instance_id)
            output, returncode = self.run(cmd, retry_count=3, debug=self.debug)
            self.say(output)
        else:
            self.say('Instance was not even created, so not terminating...')

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

    # We need to flush stdout for Jenkins:
    def say(self, s, banner=None):
        s = '{} {}'.format(self.name, s)
        if banner is not None:
            s = '\n{}\n{}\n{}'.format(banner * 50, s, banner * 50)
        self.log.debug(s)
        sys.stdout.flush()

    # Helper function for run command, in case we get back
    # funny unicode from command we are executing:
    def safe_str(self, obj):
        """ return the byte string representation of obj """
        try:
            return str(obj)
        except UnicodeEncodeError:
            # obj is unicode
            return unicode(obj).encode('unicode_escape')

    # General purpose run command:
    def run(self, cmd, hide_command=True, raiseOnFailure=True,
            retry_count=0,
            retry_sleep_secs=30, debug=False):
        try:
            xrange
        except NameError:
            xrange = range
        for i_attempt in xrange(retry_count + 1):
            if hide_command is False or debug is True:
                self.say('cmd: {0}'.format(cmd))
            output = None
            stdout = None
            stderr = None
            returncode = None
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
                output = self.safe_str(p.communicate()[0])
                returncode = p.returncode
            except Exception:
                self.say('***Error in command: {0}'.format(cmd))
                self.say('Exception:----------------')
                self.say(traceback.format_exc())
                self.say('--------------------------')
            if returncode != 0:
                # There was an error, lets retry, if possible:
                if i_attempt != retry_count:
                    # Only sleep if not end of the loop:
                    self.say('retrying command: {}, after sleeping: {}s'.format(cmd, retry_sleep_secs))
                    time.sleep(retry_sleep_secs)
                continue
            else:
                # Command was success, let's not retry:
                break

        if returncode != 0 and raiseOnFailure is True:
            self.say('***Error in command and raiseOnFailure is True so exiting. CMD:\n{0}'.format(cmd))
            all_output = output

            self.say('This is the output from that command, if any:\n{0}'.format(all_output))
            raise Exception('Command_Error')

        if debug is True:
            self.say('Debug Information:\noutput:\n{0}\nreturncode: {1}'.format(output, returncode))
        return output, returncode

    def __enter__(self):
        pass

    def __del__(self):
        self.tear_down_test()

    def __exit__(self, type, value, traceback):
        self.tear_down_test()


if __name__ == '__main__':
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