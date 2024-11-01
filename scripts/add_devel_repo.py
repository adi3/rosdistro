#!/usr/bin/env python

from __future__ import print_function
import argparse
import sys
import yaml

from sort_yaml import sort_yaml_data


def add_devel_repository(yaml_file, name, vcs_type, url, version=None):
    """
    Adds a new development repository to a given YAML file, which must be of type
    'source' or 'gbp'. It updates the file with the new repository information and
    adds it to the file's contents.

    Args:
        yaml_file (str): Used to specify the path to a YAML file that contains
            repository definitions.
        name (str): Used to identify a repository in the yaml file. It is a required
            parameter and is used to check if a repository with the same name
            already exists in the yaml file.
        vcs_type (str): Used to specify the type of version control system, such
            as 'git' or 'svn'.
        url (str): Used to specify the Uniform Resource Locator of the version
            control system repository that is being added.
        version (str | None): Optional. It specifies the version of the repository
            being added.

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
    Adds a new 'devel' repository to a given YAML file, ensuring the repository
    is of the correct type and does not already exist in the file. It also updates
    the YAML file with the new repository information.

    Args:
        yaml_file (str): Used to specify the path to a YAML file where the repository
            data is stored.
        data (Dict[str, Any]): Presumably a Python dictionary representing the
            YAML file's content, specifically the repositories section.
        name (str): Used to uniquely identify a repository within the YAML data.
            It is used to check if a repository with the same name already exists
            in the YAML data.
        vcs_type (str): Used to specify the type of version control system used
            by the repository.
        url (str): Required to be passed to the function. It represents the URL
            of the version control system repository.
        version (str | None): Used to specify the version of the repository, but
            its usage is restricted based on the value of the `vcs_type` parameter.

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
