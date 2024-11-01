#!/usr/bin/env python

from __future__ import print_function

import argparse
import shutil
import subprocess
import sys
import tempfile

from catkin_pkg.packages import find_package_paths
from rosdistro import get_distribution_file, get_index, get_index_url


def check_git_repo(url, version):
    """
    Checks if a given URL is a valid Git repository and if a specific version
    exists within it. It uses the `git ls-remote` command to query the repository
    and raises a `RuntimeError` if the URL is invalid or the version is not found.

    Args:
        url (str): Expected to be a valid Git repository URL, which can be used
            to verify the repository's existence and check for a specific version.
        version (str): Optional. It specifies the expected version of the git
            repository to be checked, and is used to verify if a specific version
            exists in the repository.

    """
    cmd = ['git', 'ls-remote', url]
    try:
        output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('not a valid git repo url')

    if version:
        for line in output.splitlines():
            if line.endswith('/%s' % version):
                return
        raise RuntimeError('version not found')


def check_hg_repo(url, version):
    """
    Checks if a given URL is a valid Mercurial repository and identifies its
    version. It raises a `RuntimeError` if the URL is invalid or if the specified
    version is not found.

    Args:
        url (str): Used as the path to a Mercurial repository. It is used by the
            `hg identify` command to determine the repository's information.
        version (str): Optional, allowing the caller to specify a specific Mercurial
            repository revision to check.

    """
    cmd = ['hg', 'identify', url]
    if version:
        cmd.extend(['-r', version])
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if not version:
            raise RuntimeError('not a valid hg repo url')
        cmd = ['hg', 'identify', url]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise RuntimeError('not a valid hg repo url')
        raise RuntimeError('version not found')


def check_svn_repo(url, version):
    """
    Verifies if a given URL is a valid Subversion repository by running the `svn
    info` command. It also checks the specified version, if provided, by adding
    the `-r` option.

    Args:
        url (str): Expected to be a valid SVN repository URL.
        version (str): Optional. It specifies the revision number to check in the
            SVN repository. If `version` is provided, it is used to extend the
            `cmd` list with the `-r` option.

    """
    cmd = ['svn', '--non-interactive', '--trust-server-cert', 'info', url]
    if version:
        cmd.extend(['-r', version])
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('not a valid svn repo url')


def clone_git_repo(url, version, path):
    """
    Clones a specified version of a Git repository from a given URL to a specified
    local path. It uses the `git clone` command with the `-b` option to clone a
    specific branch and the `-q` option to suppress output.

    Args:
        url (str): Required. It specifies the URL of the Git repository to be
            cloned. It is expected to be a valid Git repository URL.
        version (str): Used to specify the branch or tag to clone from the given
            Git repository URL.
        path (str): Used to specify the directory where the cloned repository will
            be created.

    """
    cmd = ['git', 'clone', url, '-b', version, '-q']
    try:
        subprocess.check_call(cmd, cwd=path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('not a valid git repo url')


def clone_hg_repo(url, version, path):
    """
    Clones a Mercurial repository from a specified URL to a given path, optionally
    cloning a specific version. It uses the `subprocess` module to execute Mercurial
    commands and checks for any errors during the cloning process.

    Args:
        url (str): Used to specify the URL of the Mercurial repository to be cloned.
        version (str | None): Used to specify a specific branch or revision to
            clone from the repository.
        path (str): Used to specify the local directory where the cloned Mercurial
            repository will be created.

    """
    cmd = ['hg', 'clone', url, '-q']
    if version:
        cmd.extend(['-b', version])
    try:
        subprocess.check_call(cmd, stderr=subprocess.STDOUT, cwd=path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('not a valid hg repo url')


def checkout_svn_repo(url, version, path):
    """
    Checks out a specified version of a Subversion repository to a given path using
    the `svn` command. It takes a URL, version, and path as input and raises a
    `RuntimeError` if the checkout fails or if the provided URL is not a valid
    Subversion repository.

    Args:
        url (str): Required. It specifies the URL of the SVN repository to be
            checked out.
        version (str): Optional. It specifies a revision number or a date to check
            out in the SVN repository.
        path (str): Used to specify the current working directory where the SVN
            repository will be checked out.

    """
    cmd = ['svn', '--non-interactive', '--trust-server-cert', 'checkout', url, '-q']
    if version:
        cmd.extend(['-r', version])
    try:
        subprocess.check_call(cmd, stderr=subprocess.STDOUT, cwd=path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('not a valid svn repo url')


def main(repo_type, rosdistro_name, check_for_wet_packages=False):
    """
    Checks a ROS distribution for valid repositories of a specified type, attempts
    to fetch them, and optionally checks for the presence of specific packages.
    It handles different types of version control systems (VCS) and reports errors.

    Args:
        repo_type (str | 'doc' | 'source'): Used to specify the type of repository
            to be checked.
        rosdistro_name (str): Required. It specifies the name of the ROS distribution
            for which the function will perform checks.
        check_for_wet_packages (bool): Used to determine whether the function
            should check for 'wet packages' in the cloned repositories.

    Returns:
        bool|None: True if all repositories are successfully checked and no wet
        packages are found, and False otherwise.

    """
    index = get_index(get_index_url())
    try:
        distribution_file = get_distribution_file(index, rosdistro_name)
    except RuntimeError as e:
        print("Could not load distribution file for distro '%s': %s" % (rosdistro_name, e), file=sys.stderr)
        return False

    for repo_name in sorted(distribution_file.repositories.keys()):
        sys.stdout.write('.')
        sys.stdout.flush()
        repo = distribution_file.repositories[repo_name]
        if repo_type == 'doc':
            repo = repo.doc_repository
        if repo_type == 'source':
            repo = repo.source_repository
        if not repo:
            continue
        try:
            if (repo.type == 'git'):
                check_git_repo(repo.url, repo.version)
            elif (repo.type == 'hg'):
                check_hg_repo(repo.url, repo.version)
            elif (repo.type == 'svn'):
                check_svn_repo(repo.url, repo.version)
            else:
                print()
                print("Unknown type '%s' for repository '%s'" % (repo.type, repo.name), file=sys.stderr)
                continue
        except RuntimeError as e:
            print()
            print("Could not fetch repository '%s': %s (%s) [%s]" % (repo.name, repo.url, repo.version, e), file=sys.stderr)
            continue

        if check_for_wet_packages:
            path = tempfile.mkdtemp()
            try:
                if repo.type == 'git':
                    clone_git_repo(repo.url, repo.version, path)
                elif repo.type == 'hg':
                    clone_hg_repo(repo.url, repo.version, path)
                elif repo.type == 'svn':
                    checkout_svn_repo(repo.url, repo.version, path)
            except RuntimeError as e:
                print()
                print("Could not clone repository '%s': %s (%s) [%s]" % (repo.name, repo.url, repo.version, e), file=sys.stderr)
                continue
            else:
                package_paths = find_package_paths(path)
                if not package_paths:
                    print()
                    print("Repository '%s' (%s [%s]) does not contain any wet packages" % (repo.name, repo.url, repo.version), file=sys.stderr)
                    continue
            finally:
                shutil.rmtree(path)

    print()

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Checks whether the referenced branches for the doc/source repositories exist')
    parser.add_argument('repo_type', choices=['doc', 'source'], help='The repository type')
    parser.add_argument('rosdistro_name', help='The ROS distro name')
    parser.add_argument('--check-for-wet-packages', action='store_true', help='Check if the repository contains wet packages rather then dry packages')
    args = parser.parse_args()

    if not main(args.repo_type, args.rosdistro_name, args.check_for_wet_packages):
        sys.exit(1)
