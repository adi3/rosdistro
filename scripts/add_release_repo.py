#!/usr/bin/env python

from __future__ import print_function
import argparse
import sys
import yaml

from sort_yaml import sort_yaml_data


def add_release_repository(yaml_file, name, url, version):
    """
    Adds a release repository to a YAML file of type 'gbp'. If the file is not of
    type 'gbp', it calls a specific function for 'gbp' type files and raises a
    RuntimeError for unsupported file types.

    Args:
        yaml_file (str): Used to specify the path to a YAML file.
        name (str): Used to specify the name of a release repository.
        url (str): Used to specify the URL of the release repository to be added.
        version (str): Passed to the `add_release_repository_fuerte` function.

    """
    data = yaml.load(open(yaml_file, 'r'))
    if data['type'] == 'gbp':
        add_release_repository_fuerte(yaml_file, data, name, url, version)
        return

    raise RuntimeError('The passed .yaml file is not of type "gbp" and it is not supported for Groovy or newer')


def add_release_repository_fuerte(yaml_file, data, name, url, version):
    """
    Adds a new repository to a YAML file, ensuring its name is unique and updating
    the file with the latest data. It does this by modifying the provided data and
    then writing it back to the specified YAML file.

    Args:
        yaml_file (str): Used to specify the name of the YAML file where the
            repository data will be updated.
        data (Dict[str, Any]): Represented as the current state of the YAML data
            being modified, which contains a key named 'repositories' to store a
            collection of repositories.
        name (str): Used as a key to uniquely identify a repository within the
            YAML data. It is checked to ensure it is not already present in the
            'repositories' section of the YAML data.
        url (str): Assigned to the 'url' key of a dictionary within the 'repositories'
            key of the 'data' dictionary. It represents a URL of a repository.
        version (str): Used to specify the version of the repository being added
            to the .yaml file.

    """
    if name in data['repositories']:
        raise RuntimeError('Repository with name "%s" is already in the .yaml file' % name)
    data['repositories'][name] = {
        'url': url,
        'version': version,
    }
    sort_yaml_data(data)
    with open(yaml_file, 'w') as out_file:
        yaml.dump(data, out_file, default_flow_style=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert a git-buildpackage repository into the .yaml file.')
    parser.add_argument('yaml_file', help='The yaml file to update')
    parser.add_argument('name', help='The unique name of the repo')
    parser.add_argument('url', help='The url of the GBP repository')
    parser.add_argument('version', help='The version')
    args = parser.parse_args()

    try:
        add_release_repository(args.yaml_file, args.name, args.url, args.version)
    except Exception as e:
        print(str(e), file=sys.stderr)
        exit(1)
