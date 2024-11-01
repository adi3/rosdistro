#!/usr/bin/env python

from __future__ import print_function
import argparse
import os
import sys
import yaml


def convert_yaml_to_rosinstall(yaml_file, rosinstall_file):
    """
    Converts a YAML file to a ROSinstall file by loading the YAML data, converting
    it to ROSinstall format, and then dumping the converted data to a new ROSinstall
    file.

    Args:
        yaml_file (str): Representing the path to a YAML file.
        rosinstall_file (str): Designated to specify the path to the output file
            where the converted ROSinstall data will be written.

    """
    data = yaml.load(open(yaml_file, 'r'))
    data = convert_yaml_data_to_rosinstall_data(data)
    with open(rosinstall_file, 'w') as out_file:
        yaml.dump(data, out_file, default_flow_style=False)


def convert_yaml_data_to_rosinstall_data(data):
    """
    Converts YAML data representing repositories into ROSinstall data format, which
    is a standardized format for specifying dependencies in ROS projects. It
    iterates over repository names, extracts relevant information, and constructs
    ROSinstall data.

    Args:
        data (Dict[str, Any]): Expected to have a specific structure, including a
            key named 'repositories', which contains another dictionary with names
            of repositories as keys and their corresponding values as values.

    Returns:
        List[Dict[str,str|int]]: A list of dictionaries where each dictionary
        represents a repository.

    """
    rosinstall_data = []
    for name in sorted(data['repositories'].keys()):
        values = data['repositories'][name]
        repo = {}
        repo['local-name'] = name
        repo['uri'] = values['url']
        if 'version' in values:
            repo['version'] = values['version']
        # fallback type is git for gbp repositories
        vcs_type = values['type'] if 'type' in values else 'git'
        rosinstall_data.append({vcs_type: repo})
    return rosinstall_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert a .yaml file into a .rosinstall file.')
    parser.add_argument('yaml_file', help='The .yaml file to convert')
    parser.add_argument('rosinstall_file', nargs='?', help='The generated .rosinstall file (default: same name as .yaml file except extension)')
    args = parser.parse_args()

    if args.rosinstall_file is None:
        path_without_ext, _ = os.path.splitext(args.yaml_file)
        args.rosinstall_file = path_without_ext + '.rosinstall'

    try:
        convert_yaml_to_rosinstall(args.yaml_file, args.rosinstall_file)
    except Exception as e:
        print(str(e), file=sys.stderr)
        exit(1)
