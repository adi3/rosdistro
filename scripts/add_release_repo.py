#!/usr/bin/env python

from __future__ import print_function
import argparse
import sys
import yaml

from sort_yaml import sort_yaml_data


def add_release_repository(yaml_file, name, url, version):
    """
    Adds a release repository to a Groovy Buildpack (GBP) project specified in a
    YAML file. It checks the YAML file type and if it's GBP, calls the
    `add_release_repository_fuerte` function to perform the addition.

    Args:
        yaml_file (str): The path to a YAML file.
        name (str): Used to specify the name of the release repository being added
            to the YAML file.
        url (str): Used to specify the URL of the repository to be added.
        version (str): Used to specify the version of the repository being added.

    """
    data = yaml.load(open(yaml_file, 'r'))
    if data['type'] == 'gbp':
        add_release_repository_fuerte(yaml_file, data, name, url, version)
        return

    raise RuntimeError('The passed .yaml file is not of type "gbp" and it is not supported for Groovy or newer')


def add_release_repository_fuerte(yaml_file, data, name, url, version):
    """
    Adds a new release repository to a YAML file, ensuring the repository name is
    unique and updating the YAML data and file accordingly.

    Args:
        yaml_file (str): A path to a YAML file where the repository data will be
            written after updating.
        data (Dict[str, Any]): Represented as the contents of a YAML file, which
            is a nested dictionary data structure. It contains a key 'repositories'
            that holds a mapping of repository names to their corresponding data.
        name (str): Used to uniquely identify a release repository in the data
            structure. It is checked to prevent duplicate repository names in the
            .yaml file.
        url (str): Used to specify the URL of a repository, which is then stored
            in the 'repositories' data structure under the specified 'name'.
        version (str): Stored in a dictionary within the 'repositories' list under
            the key 'version'.

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
