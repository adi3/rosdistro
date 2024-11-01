#!/usr/bin/env python3

# Copyright (c) 2017, Open Source Robotics Foundation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Willow Garage, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import argparse
import os
import sys
from github import Github, UnknownObjectException


def detect_repo_hook(repo, cb_url):
    """
    Checks if a specified webhook URL is configured for a given repository. It
    iterates through the repository's hooks and returns True if the specified URL
    matches any hook's configuration, indicating its presence. Otherwise, it returns
    False, indicating its absence.

    Args:
        repo (GitRepository): Expected to have a `get_hooks` method that returns
            a list of hooks in the repository, allowing iteration over them.
        cb_url (str): Used to store the URL of a specific webhook.

    Returns:
        bool: True if a GitHub webhook with the specified `cb_url` is found in the
        repository, and False otherwise.

    """
    for hook in repo.get_hooks():
        if hook.config.get('url') == cb_url:
            return True
    return False


class GHPRBHookDetector(object):
    """
    Detects and verifies the presence of GitHub hooks in repositories, ensuring
    that repositories with push access or admin access have a manual hook configuration
    in place.

    Attributes:
        callback_url (str): Initialized in the `__init__` method to store a URL.
        gh (Githubinstance): Instantiated with the `Github` class from the `github`
            library, passing the `github_user` and `github_token` as arguments.

    """
    def __init__(self, github_user, github_token, callback_url):
        """
        Initializes the class instance with the provided GitHub user, token, and
        callback URL, setting the callback URL as an instance variable and creating
        a Github object using the provided credentials.

        Args:
            github_user (str): Required to authenticate with GitHub. It is expected
                to be the GitHub username or the full GitHub user ID.
            github_token (str): Required to authenticate with the GitHub API. It
                represents a personal access token, which grants the application
                permission to access the GitHub account associated with the provided
                `github_user`.
            callback_url (str): Assigned to an instance variable of the same name.
                It represents the URL to which the GitHub API will send callbacks
                to notify the application of certain events.

        """
        self.callback_url = callback_url
        self.gh = Github(github_user, github_token)

    def get_repo(self, username, reponame):
        """
        Retrieves a GitHub repository by username and repository name.

        Args:
            username (str): Used to specify the username of the GitHub user whose
                repository is to be accessed.
            reponame (str): Used to identify the name of a specific repository on
                GitHub.

        Returns:
            Any: Either the `repo` object if the function is successful or `None`
            if the repository is unknown.

        """
        try:
            repo = self.gh.get_user(username).get_repo(reponame)
        except UnknownObjectException as ex:
            print(
                'Failed to access repo [ %s/%s ] Reason %s'
                % (username, reponame, ex),
                file=sys.stderr
                )
            return None
        return repo

    def check_repo_for_access(self, repo, errors, strict=False):
        """
        Determines whether a repository has access to push changes and whether a
        manual hook configuration is present, based on its permissions and the
        outcome of a hook detection attempt.

        Args:
            repo (object): Representing a repository, likely an instance of a class
                that encapsulates information about a Git repository.
            errors (List[str]): Used to accumulate error messages that occur during
                the execution of the function.
            strict (bool): Determining the behavior of the function when push
                access is detected but unable to verify manual hook configuration.

        Returns:
            bool|None: `True` if push access exists and the hook is detected or
            admin access exists, or if push access exists but hook detection fails
            and strict mode is not activated. Otherwise, it returns `False` in
            strict mode or `True` with an error message in non-strict mode.

        """
        push_access = repo.permissions.push
        admin_access = repo.permissions.admin
        try:
            hook_detected = detect_repo_hook(repo, self.callback_url)
        except UnknownObjectException as ex:
            errors.append('Unable to check repo [ %s ] for hooks: Error: %s' % (repo.full_name, ex))
            hook_detected = False
        if push_access and hook_detected or admin_access:
            return True
        if push_access and not hook_detected:
            print(
                'Warning: Push access detected but unable to verify manual hook '
                'configuration for repo [ %s ]. Please visit ' % repo.full_name +
                'http://wiki.ros.org/buildfarm/Pull%20request%20testing '
                'and make sure hooks are setup.',
                file=sys.stderr)
            if strict:
                return False
            else:
                errors.append(
                    'Warning: Push access detected but unable to verify manual hook '
                    'configuration for repo [ %s ]. Please visit ' % repo.full_name +
                    'http://wiki.ros.org/buildfarm/Pull%20request%20testing '
                    'and make sure hooks are setup.')
                return True


def check_hooks_on_repo(user, repo, errors, hook_user='ros-pull-request-builder',
        callback_url='http://build.ros.org/ghprbhook/', token=None, strict=False):
    """
    Checks if a GitHub repository has sufficient permissions to set up pull request
    builds. It verifies access to hooks using the GHPRBHookDetector class and
    returns True if access is granted, False otherwise.

    Args:
        user (str): Required. It represents the GitHub user or organization for
            which the repository is being checked.
        repo (str): Used to specify the name of the repository on GitHub.
        errors (List[Exception]): Passed to the `check_repo_for_access` method of
            `ghprb_detector` to store any errors that occur during the check for
            hooks access.
        hook_user (str): Defaulted to `'ros-pull-request-builder'`.
        callback_url (str): Required and defaults to `'http://build.ros.org/ghprbhook/'`.
            It is used by the `GHPRBHookDetector` class to set the callback URL
            for the GitHub hook.
        token (str | None): Used to authenticate the GitHub repository. It is an
            optional parameter that defaults to None.
        strict (bool): Used by the `ghprb_detector.check_repo_for_access` method
            to determine the level of access verification required.

    Returns:
        bool: True if the repository has enough permissions to set up pull request
        builds, False otherwise.

    """
    ghprb_detector = GHPRBHookDetector(hook_user, token, callback_url)
    test_repo = ghprb_detector.get_repo(user, repo)

    if test_repo:
        hooks_ok = ghprb_detector.check_repo_for_access(test_repo, errors, strict=strict)
        if hooks_ok:
            print('Passed ghprb_detector check for hooks access'
                  ' for repo [ %s ]' % test_repo.full_name)
            return True
        else:
            print('ERROR: Not enough permissions to setup pull request'
                  ' builds for repo [ %s ] ' % (test_repo.full_name) +
                  'Please see http://wiki.ros.org/buildfarm/Pull%20request%20testing',
                  file=sys.stderr
                  )
            return False
    else:
        print(
            'ERROR: No github repository found at %s/%s' % (user, repo),
            file=sys.stderr
        )
        return False


def main():
    """A simple main for testing via command line."""
    parser = argparse.ArgumentParser(
        description='A manual test for ros-pull-request-builder access'
                    'to a GitHub repo.')
    parser.add_argument('user', type=str)
    parser.add_argument('repo', type=str)
    parser.add_argument('--callback-url', type=str,
        default='http://build.ros.org/ghprbhook/')
    parser.add_argument('--hook-user', type=str,
        default='ros-pull-request-builder')
    parser.add_argument('--password-env', type=str,
        default='ROSGHPRB_TOKEN')

    args = parser.parse_args()

    password = os.getenv(args.password_env)
    if not password:
        parser.error(
            'OAUTH Token with hook and organization read access'
            'required in ROSGHPRB_TOKEN environment variable')
    errors = []
    result = check_hooks_on_repo(
        args.user,
        args.repo,
        errors,
        args.hook_user,
        args.callback_url,
        password)
    if errors:
        print('Errors detected:', file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    if result:
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
