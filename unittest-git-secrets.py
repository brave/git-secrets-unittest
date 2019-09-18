#!/usr/bin/env python3

# Copyright (c) 2019 Brave Software

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

"""

Validate both git-secrets and git pre-commit hook functions correctly.

This program will validate that git-secrets functions correctly by utilizing the
git pre-commit hook for the user executing the test.

We will create a new git repository, write a prohibited pattern to a file, then
attempt to perform a git commit in that repo. This should trigger git-secrets to
warn of prohibited patterns found in the commit. A succesful result will display
'ERROR' in the output because it found a prohibited pattern, and will also
display 'OK' on the last line.

NOTE: You must have the following pre-reqs already configured:
* Python 3.4 or above
* The tool [git-secrets](https://github.com/awslabs/git-secrets) must be
  installed and configured to recognize AWS patterns
* You must setup a Git pre-commit hook:
  * Use the Git config variable
    'core.hooksPath'(https://github.com/awslabs/git-secrets#advanced-configuration)(preferred),
    or the Git config variable
    'init.templateDir'(https://git-scm.com/docs/git-init#_template_directory).

"""

import argparse
import logging
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from argparse import RawTextHelpFormatter
from string import ascii_uppercase, ascii_lowercase, digits


class ForegroundColor():
    """Ascii colors used for messages."""

    RED = "\033[1;31;40m"
    GREEN = "\033[1;32;40m"
    RESET = "\33[0m"


class TestAwsPatterns(object):
    """Utility functions for testing AWS patterns."""

    def __init__(self, debug):
        self.debug = debug

    def create_repo(self, path):
        p = pathlib.Path(path)
        git_dir_path = p / '.git'
        if os.path.isdir(git_dir_path):
            logging.error("Git directory \'{}\' already exists! Exiting...".format(git_dir_path))

        cmd = "git init {}".format(path)
        logging.debug("Running command: \'{}\'".format(cmd))  # DEBUG
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            logging.debug(output.decode('utf-8'))
            self.disable_gpgsign(path)
            if self.debug:
                git_config_path = p / '.git' / 'config'
                with open(git_config_path, 'r') as f:
                    contents = f.read()
                    logging.debug(".git/config file contents: \n{}".format(contents))
        except subprocess.CalledProcessError as cpe:
            logging.error('Command \'{}\' return code: {}'.format(cmd, cpe.returncode))
            logging.error('Command output: {}'.format(cpe.output.decode('utf-8')))
            return False

    def disable_gpgsign(self, path):
        p = pathlib.Path(path)
        git_config_path = p / '.git' / 'config'

        gpgsign_config_string = '{}\n\t{}'.format('[commit]', 'gpgsign = false')

        with open(git_config_path, 'a') as f:
            f.write(gpgsign_config_string)

    def trigger_hook(self, f):
        marker = False
        cmd = 'git add {}'.format(f)
        logging.debug("Running command: \'{}\'".format(cmd))  # DEBUG
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as cpe:
            logging.error("Could not run command \'{}\': {}".format(cmd, cpe.output.decode('utf-8')))

        cmd = 'git commit -m \'{}\''.format("test pre-commit hook")
        logging.debug("Running command: \'{}\'".format(cmd))  # DEBUG
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            marker = True
        except subprocess.CalledProcessError as cpe:
            logging.info('Command \'{}\' return code: {}'.format(cmd, cpe.returncode))
            logging.info('Command output:\n {}{}{}'.format(ForegroundColor.GREEN, cpe.output.decode('utf-8'),
                                                           ForegroundColor.RESET))

        return marker

    def remove_repo(self, path):
        try:
            shutil.rmtree(path)
        except Exception as e:
            logging.error("Cannot remove directory \'{}\': \'{}\'".format(path, e))
            return False

    def generate_random_aws_secret_key(self):
        chars = ascii_uppercase + ascii_lowercase + digits + '/' + '+' + '='
        key = ''.join(random.choice(chars) for _ in range(40))
        return key

    def generate_random_aws_access_key(self):
        chars = ascii_uppercase + digits
        key = 'AKIA' + ''.join(random.choice(chars) for _ in range(16))
        return key

    def which_git_secrets(self):
        git_secrets = 'git-secrets'
        found = shutil.which(git_secrets)
        if found is None:
            logging.error("{} is not found in the path!".format(git_secrets))
            exit(1)
        else:
            if not os.access(found, os.X_OK):
                logging.error("{} is not executable!".format(found))
                exit(1)

    def scan_git_secrets(self, path):
        cmd = 'git-secrets --scan ' + path
        logging.debug("Running command: \'{}\'".format(cmd))  # DEBUG
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            logging.debug(output.decode('utf-8'))
        except subprocess.CalledProcessError as cpe:
            logging.info('Command \'{}\' return code: {}'.format(cmd, cpe.returncode))
            logging.info('Command output: {}{}{}'.format(ForegroundColor.GREEN, cpe.output.decode('utf-8'),
                                                         ForegroundColor.RESET))
            return False


class Test_01_GitPreCommitHook(unittest.TestCase):
    DEBUG = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo_path = tempfile.mkdtemp()
        self.outfile = 'test.txt'
        self.debug = False
        if self.DEBUG:
            self.debug = True

    def setUp(self):
        self.g1 = TestAwsPatterns(self.debug)
        self.g1.which_git_secrets()
        if self.g1.create_repo(self.repo_path) is not False:
            p = pathlib.Path(self.repo_path)
            outfile_path = p / self.outfile
            prohibited_pattern = 'aws_secret_access_key = {}'.format(self.g1.generate_random_aws_secret_key())
            with open(outfile_path, 'w') as f:
                f.write(prohibited_pattern)

    def test_git_pre_commit_hook(self):
        saved_path = os.getcwd()
        try:
            os.chdir(self.repo_path)
            logging.debug('Changed directory to \"{}\"'.format(self.repo_path))
        except OSError as ose:
            message = ('Error: could not change directory to {}: {}'.format(self.repo_path, ose))
            logging.error(message)
        self.assertFalse(self.g1.trigger_hook(self.outfile))
        try:
            os.chdir(saved_path)
            logging.debug('Changed directory to \"{}\"'.format(saved_path))
        except OSError as ose:
            message = ('Error: could not change directory to {}: {}'.format(saved_path, ose))
            logging.error(message)

    def tearDown(self):
        if self.g1.remove_repo(self.repo_path) is False:
            logging.error("Error: Cannot remove the directory, you will need to do this manually: \'{}\'"
                          .format(self.repo_path))


def parse_args():
    desc = """

Validate both git-secrets and git pre-commit hook functions correctly.

This program will validate that git-secrets functions correctly by utilizing the
git pre-commit hook for the user executing the test.

We will create a new git repository, write a prohibited pattern to a file, then
attempt to perform a git commit in that repo. This should trigger git-secrets to
warn of prohibited patterns found in the commit. A succesful result will display
'ERROR' in the output because it found a prohibited pattern, and will also
display 'OK' on the last line.

NOTE: You must have the following pre-reqs already configured:
* Python 3.4 or above
* The tool [git-secrets](https://github.com/awslabs/git-secrets) must be
  installed and configured to recognize AWS patterns
* You must setup a Git pre-commit hook:
  * Use the Git config variable
    'core.hooksPath'(https://github.com/awslabs/git-secrets#advanced-configuration)(preferred),
    or the Git config variable
    'init.templateDir'(https://git-scm.com/docs/git-init#_template_directory).

"""

    parser = argparse.ArgumentParser(description=desc, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug output')
    try:
        options = parser.parse_args()
        return options
    except:                     # noqa: E722
        sys.exit(0)


def main():

    # Pathlib is available as a stdlib function in Python 3.4, so we want to
    # encourage upgrading to a recent version of Python in order to use this tool.
    if not sys.version_info >= (3, 4):
        print("ERROR: Required minimum Python version is 3.4! Exiting...")
        exit(1)

    args = parse_args()
    if args.debug:
        sys.argv = sys.argv[:1]     # avoid passing the debug argument to unittest.main()
        Test_01_GitPreCommitHook.DEBUG = True
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(message)s')

    unittest.main()


if __name__ == '__main__':
    sys.exit(main())
