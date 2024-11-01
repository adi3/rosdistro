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
    Verifies whether a given URL is a valid Git repository and checks for the
    existence of a specific version within it. It raises a `RuntimeError` if the
    URL is invalid or the version is not found.

    Args:
        url (str): Interpreted by the `git ls-remote` command. It represents the
            URL of a Git repository.
        version (str): Optional, allowing the caller to specify a particular version
            of the Git repository to search for.

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
    Checks if a given URL is a valid Mercurial repository and if a specific version
    exists within it. It uses the `hg identify` command to verify the repository
    and version.

    Args:
        url (str): Representing the URL of a Mercurial repository.
        version (str | None): Optional. When provided, it specifies a specific
            revision to check in the Mercurial repository. When not provided, the
            function checks the latest revision.

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
    Checks if a given URL is a valid Subversion repository by running the `svn
    info` command with the option to trust server certificates. It also supports
    checking a specific version of the repository.

    Args:
        url (str): Used to specify the path to a Subversion (SVN) repository. It
            is a required argument and is expected to be a valid URL that can be
            used to access an SVN repository.
        version (str): Optional.

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
    Clones a Git repository from a specified URL into a local directory, targeting
    a specific branch or version, and raises a `RuntimeError` if the cloning process
    fails.

    Args:
        url (str): Expected to be the URL of a Git repository. It is used to clone
            a specific branch or version of the repository. The URL typically
            starts with 'git@' or 'https://'.
        version (str): Used to specify the branch or tag of the Git repository to
            clone.
        path (str): Used to specify the directory where the Git repository will
            be cloned.

    """
    cmd = ['git', 'clone', url, '-b', version, '-q']
    try:
        subprocess.check_call(cmd, cwd=path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('not a valid git repo url')


def clone_hg_repo(url, version, path):
    """
    Clones a specified version of a Mercurial repository from a given URL to a
    specified local path, using the `hg` command-line tool. It raises a `RuntimeError`
    if the cloning process fails or the URL is not a valid Mercurial repository.

    Args:
        url (str): A Mercurial repository URL from which a clone will be made.
        version (str | None): Used to specify a particular branch or revision to
            clone from the Mercurial repository.
        path (str): Used as the current working directory for the `subprocess.check_call`
            function. It specifies the directory where the Mercurial repository
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
    Checks out a specified version of a Subversion (SVN) repository at a given URL
    to a specified path using the `svn` command. It raises a `RuntimeError` if the
    checkout fails due to an invalid SVN repository URL.

    Args:
        url (str): Required, specifying the URL of the Subversion repository to
            be checked out.
        version (str | None): Used to specify a revision number or revision range
            for the SVN checkout operation. If `version` is not provided, the SVN
            client will check out the latest revision.
        path (str): Used as the current working directory for the `subprocess.check_call`
            call.

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
    Checks the availability of repositories for a given ROS distribution, clones
    them if necessary, and verifies the presence of "wet" packages within the
    cloned repositories.

    Args:
        repo_type (str | 'doc' | 'source'): Used to determine which repository to
            access within a given repository. It can be either 'doc' for documentation
            or 'source' for source code.
        rosdistro_name (str): Used to identify the ROS (Robot Operating System)
            distribution for which the function is to perform operations.
        check_for_wet_packages (bool): Optional.

    Returns:
        bool: True if all repositories are successfully checked and False otherwise.

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
