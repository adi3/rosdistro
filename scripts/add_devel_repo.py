#!/usr/bin/env python

from __future__ import print_function
import argparse
import sys
import yaml

from sort_yaml import sort_yaml_data


def add_devel_repository(yaml_file, name, vcs_type, url, version=None):
    """
    Adds a new repository to a ROS (Robot Operating System) .yaml file, specifying
    the repository name, version control system, URL, and version.

    Args:
        yaml_file (str): The path to a YAML file that contains repository information.
        name (str): Used to uniquely identify a repository within the .yaml file.
        vcs_type (str): Used to specify the type of version control system for the
            repository being added.
        url (str): Used to specify the URL of the repository being added.
        version (str | None): Optional. It specifies the version of the repository
            to be added.

    """
    data = yaml.load(open(yaml_file, 'r'))
    if data['type'] == 'gbp':
        add_devel_repository_fuerte(yaml_file, data, name, vcs_type, url, version)
        return

    if data['type'] != 'source':
        raise RuntimeError('The passed .yaml file is neither of type "source" nor "gbp"')

    if name in data['repositories']:
        raise RuntimeError('Repository with name "%s" is already in the .yaml file' % name)

    data['repositories'][name] = {
        'type': vcs_type,
        'url': url,
        'version': version,
    }
    try:
        from rosdistro.verify import _to_yaml, _yaml_header_lines
    except ImportError as e:
        raise ImportError(str(e) + ' - you need to install the latest version of python-rosdistro.')
    data = _to_yaml(data)
    data = '\n'.join(_yaml_header_lines('source')) + '\n' + data
    with open(yaml_file, 'w') as f:
        f.write(data)


def add_devel_repository_fuerte(yaml_file, data, name, vcs_type, url, version):
    """
    Adds a new development repository to a YAML file. It validates the repository
    type, checks for duplicate names, and updates the YAML data before writing it
    back to the file.

    Args:
        yaml_file (str): Used to specify the name of the YAML file where the
            repository information will be written to.
        data (Dict[str, object]): Represented as a dictionary containing key-value
            pairs, where 'repositories' is a key that holds another dictionary of
            repository configurations.
        name (str): Used to uniquely identify a repository within the YAML file.
            It is used as a key in the `data['repositories']` dictionary.
        vcs_type (str | None): Used to specify the type of version control system
            used by the repository. It can be one of the supported types, such as
            'git', 'svn', etc.
        url (str): Used to specify the URL of the version control system where the
            repository is located.
        version (str | None): Used to specify the version of a repository. It is
            required for all repository types except SVN, but when it is provided,
            SVN repositories are invalid.

    """
    if data['type'] != 'devel':
        raise RuntimeError('The passed .yaml file is not of type "devel"')
    if name in data['repositories']:
        raise RuntimeError('Repository with name "%s" is already in the .yaml file' % name)
    values = {
        'type': vcs_type,
        'url': url,
    }
    if version is None and vcs_type != 'svn':
        raise RuntimeError('All repository types except SVN require a version attribute')
    if version is not None:
        if vcs_type == 'svn':
            raise RuntimeError('SVN repository must not have a version attribute but must contain the version in the URL')
    values['version'] = version
    data['repositories'][name] = values
    sort_yaml_data(data)
    with open(yaml_file, 'w') as out_file:
        yaml.dump(data, out_file, default_flow_style=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert a repository into the .yaml file.')
    parser.add_argument('yaml_file', help='The yaml file to update')
    parser.add_argument('name', help='The unique name of the repo')
    parser.add_argument('type', help='The type of the repository (i.e. "git", "hg", "svn")')
    parser.add_argument('url', help='The url of the repository')
    parser.add_argument('version', nargs='?', help='The version')
    args = parser.parse_args()

    try:
        add_devel_repository(args.yaml_file, args.name, args.type, args.url, args.version)
    except Exception as e:
        print(str(e), file=sys.stderr)
        exit(1)
