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
    and raises a `RuntimeError` if the URL or version is invalid.

    Args:
        url (str): Used as the base URL for a Git repository. It is passed to the
            `git ls-remote` command to check the validity of the repository.
        version (str): Optional, indicating a specific version of the repository
            to look for.

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
    Verifies if a given URL is a valid Mercurial repository and checks for the
    existence of a specified version. It uses the `hg identify` command to check
    the repository and version.

    Args:
        url (str): Used to specify the URL of the Mercurial repository to be checked.
        version (str | None): Optional, indicating a specific revision in the
            Mercurial repository to check.

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
    Checks if a given URL is a valid SVN repository by attempting to retrieve its
    information using the `svn` command. It also allows specifying a specific
    version to check.

    Args:
        url (str): Used to specify the URL of the SVN repository to be checked.
        version (str): Optional. It specifies a particular revision of the SVN
            repository to check. If `version` is provided, it is used to extend
            the `cmd` list with the `-r` option and the version number.

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
    Clones a Git repository from a specified URL and version into a specified local
    path, suppressing output (-q option) and raising an exception if the clone
    operation fails.

    Args:
        url (str): Expected to be a valid URL of a Git repository.
        version (str): Interpreted as a branch name. It specifies the Git branch
            to be cloned from the provided URL.
        path (str): Used as the current working directory for the `git clone`
            command. It specifies the location where the cloned repository will
            be created.

    """
    cmd = ['git', 'clone', url, '-b', version, '-q']
    try:
        subprocess.check_call(cmd, cwd=path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('not a valid git repo url')


def clone_hg_repo(url, version, path):
    """
    Clones a Mercurial repository from a specified URL, optionally cloning a
    specific version, and raises a `RuntimeError` if the cloning process fails.

    Args:
        url (str): Used to specify the URL of the Mercurial repository to be cloned.
        version (str): Optional. It specifies a branch name to clone, allowing the
            function to clone a specific version of the repository.
        path (str): Used to specify the directory where the Mercurial repository
            will be cloned.

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
    Checks out a specified version of a Subversion repository to a given path. It
    takes a URL, version (optional), and path as input, and raises a `RuntimeError`
    if the checkout fails due to an invalid URL.

    Args:
        url (str): Expected to be a valid Subversion repository URL.
        version (str): Optional. It is used to specify a particular revision of
            the SVN repository to check out.
        path (str): Used to specify the local directory where the SVN repository
            will be checked out.

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
    Checks the availability of repositories for a given ROS distribution, and for
    a specified repository type. It fetches and clones the repositories, and
    optionally checks for the presence of 'wet' packages.

    Args:
        repo_type (str): Used to determine which repository (doc or source) to
            access within a given distribution file.
        rosdistro_name (str): Used to specify the name of the ROS distribution
            file, which is used to load the distribution file and then check the
            repositories for the specified distribution.
        check_for_wet_packages (bool): Set to False by default. It determines
            whether the function should check for the presence of "wet packages"
            in the cloned repositories.

    Returns:
        bool: True if at least one repository is successfully checked and False
        otherwise, indicating a potential issue with the distribution file or a repository.

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
