#!/usr/bin/env python

from __future__ import print_function
import argparse
import sys
import yaml

from sort_yaml import sort_yaml_data


def add_devel_repository(yaml_file, name, vcs_type, url, version=None):
    """
    Adds a new repository to a specified YAML file based on the ROS (Robot Operating
    System) distribution format. It handles different repository types, including
    'gbp' and 'source', and updates the YAML file accordingly.

    Args:
        yaml_file (str): Used to specify the path to a YAML file where repository
            information is stored. It is used to read and modify this file.
        name (str): Used to specify the name of the repository to be added to the
            .yaml file.
        vcs_type (str): Used to specify the type of version control system, such
            as 'git' for Git or 'svn' for Subversion.
        url (str): Required. It represents the URL of the version control system
            repository to be added.
        version (str | None): Optional. It specifies the version of the repository
            being added. If not provided, the version will default to a value of
            None.

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
    Adds a new development repository to a YAML file, validates the data and
    repository type, and updates the YAML file accordingly. It checks for existing
    repositories and version attributes based on the repository type.

    Args:
        yaml_file (str): Used to specify the path to a YAML file that stores data,
            which is modified by the function.
        data (Dict[str, Any]): Expected to contain a dictionary with a 'repositories'
            key, which itself contains a dictionary of repository settings.
        name (str): Used to identify a repository by a unique name within the
            `.yaml` file. It is used to check for duplicate repository names and
            to store the repository information in the `.yaml` file.
        vcs_type (str): Used to specify the type of version control system being
            used for the repository.
        url (str): Used to define the URL of the version control system being added
            to the repository.
        version (str | None): Used to specify the version of the repository.

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
