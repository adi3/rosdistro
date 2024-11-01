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
    Checks if a specified callback URL exists in the configuration of any hook in
    a given repository. It iterates over all hooks, comparing their URLs to the
    specified callback URL, and returns True if a match is found, False otherwise.

    Args:
        repo (GitRepository | object): Represented as a Git repository object that
            has a `get_hooks()` method, which returns a list of hooks in the repository.
        cb_url (str): Used to specify the URL of a webhook, likely a GitHub Check-in
            hook, that is to be detected in the provided repository.

    Returns:
        bool: True if the specified repository contains a webhook with the given
        callback URL, and False otherwise.

    """
    for hook in repo.get_hooks():
        if hook.config.get('url') == cb_url:
            return True
    return False


class GHPRBHookDetector(object):
    """
    Detects whether a GitHub repository has a pull request hook configured, based
    on its permissions and a specified callback URL.

    Attributes:
        callback_url (str): Initialized in the `__init__` method with the
            `callback_url` parameter passed to it.
        gh (GithubObject): Initialized in the `__init__` method using the `Github`
            class from the `github` library, with the provided `github_user` and
            `github_token`.

    """
    def __init__(self, github_user, github_token, callback_url):
        """
        Initializes an instance of the GHPRBHookDetector class, setting the callback
        URL and authenticating with the GitHub API using the provided GitHub user
        and token.

        Args:
            github_user (str): Required to authenticate with the GitHub API,
                representing the GitHub username or the user's GitHub API token.
            github_token (str): Used to authenticate with the GitHub API. It
                represents a token obtained from GitHub for authorization purposes,
                typically created through the GitHub Developer Settings.
            callback_url (str): Assigned to an instance variable `callback_url`.
                It appears to represent a URL that will be used to receive callbacks,
                likely related to GitHub events or authentication.

        """
        self.callback_url = callback_url
        self.gh = Github(github_user, github_token)

    def get_repo(self, username, reponame):
        """
        Fetches a GitHub repository based on the provided username and repository
        name. If the repository does not exist, it catches the exception, prints
        an error message to standard error, and returns None.

        Args:
            username (str): Used to specify the username of a GitHub user. It is
                used to access the user's repositories on GitHub.
            reponame (str): Used to identify the name of a repository.

        Returns:
            Any: Either a GitHub repository object or None, depending on whether
            the specified repository exists and can be accessed.

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
        Determines whether a repository has sufficient permissions for access. It
        checks for push access with or without a detected hook, or admin access.
        It returns True if access is granted, and False if strict mode is enabled
        and push access is detected without a hook.

        Args:
            repo (Repository): Used to represent a repository.
            errors (List[str]): Used to accumulate error messages related to the
                repository access check. It is appended with error messages in
                case of exceptions or when push access is detected without manual
                hook configuration.
            strict (bool): Determining its effect in the function.
                The `strict` parameter determines the function's behavior when
                push access is detected but hook configuration cannot be verified.
                If `strict` is True, the function returns False; otherwise, it
                returns True and appends a warning message to the `errors` list.

        Returns:
            bool|None: Either `True` if push access and either hook detection or
            admin access are present, or `False` if strict mode is enabled and
            push access is present but hook detection fails.

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
    Checks if a GitHub repository has sufficient permissions for pull request
    builds, using a GHPRBHookDetector. It takes user, repository, error list, and
    other parameters to determine if the repository has the required access.

    Args:
        user (str): Used to identify the owner of a GitHub repository. It is a
            required parameter.
        repo (str): Required. It specifies the name of the repository on GitHub.
        errors (List[Exception]): Used to accumulate any exceptions encountered
            during the execution of the function.
        hook_user (str): Defined with a default value of `'ros-pull-request-builder'`.
        callback_url (str): Used as a URL for the GHPRB hook, specifically 'http://build.ros.org/ghprbhook/'.
        token (str | None): Optional. It is used to authenticate a GitHub API
            request when detecting GitHub pull request builder hooks.
        strict (bool): Used by the `ghprb_detector.check_repo_for_access` method
            to determine how to handle errors when checking permissions for
            repository access.

    Returns:
        bool: True if the function successfully checks for hooks access on the
        specified repository and False otherwise.

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
