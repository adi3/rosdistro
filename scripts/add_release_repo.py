#!/usr/bin/env python

from __future__ import print_function
import argparse
import sys
import yaml

from sort_yaml import sort_yaml_data


def add_release_repository(yaml_file, name, url, version):
    """
    Loads a YAML file, checks if its type is 'gbp', and if so, calls the
    `add_release_repository_fuerte` function with the same parameters. If the type
    is not 'gbp', it raises a RuntimeError with a specific error message.

    Args:
        yaml_file (str): Representing the path to a YAML file containing configuration
            data.
        name (str): Used to specify the name of the release repository to be added
            to the YAML file.
        url (str): Used to specify the URL of a release repository.
        version (str): Required to specify the version of the release repository.

    """
    data = yaml.load(open(yaml_file, 'r'))
    if data['type'] == 'gbp':
        add_release_repository_fuerte(yaml_file, data, name, url, version)
        return

    raise RuntimeError('The passed .yaml file is not of type "gbp" and it is not supported for Groovy or newer')


def add_release_repository_fuerte(yaml_file, data, name, url, version):
    """
    Adds a new repository to a YAML file. It checks for existing repository names,
    updates the data, sorts it, and writes the changes to the YAML file.

    Args:
        yaml_file (str): Used to specify the path to a YAML file where repository
            information is stored.
        data (Dict[str, Any]): Represented as a dictionary containing a key
            'repositories' which is also a dictionary mapping repository names to
            their respective configurations.
        name (str): Used as a key in the 'repositories' dictionary of the data
            structure to uniquely identify a repository.
        url (str): Used to specify the URL of the repository being added to the
            .yaml file.
        version (str): Used to store the version of the repository in the
            'repositories' dictionary.

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
