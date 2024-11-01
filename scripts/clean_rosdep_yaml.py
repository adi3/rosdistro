#!/usr/bin/env python

import yaml
import argparse
import re
import io

dont_bracket = ['uri', 'md5sum']

def paddify(s, l):
    """
    Formats a given string `s` by indenting each line except the last one with a
    specified number of spaces `l`, effectively padding the content.

    Args:
        s (str): Representing a string of newline-separated lines.
        l (int): Used to determine the number of spaces to be used for padding
            each line of text.

    Returns:
        str: A string consisting of the input lines padded with a specified number
        of spaces.

    """
    a = s.split('\n')
    buf = ''
    pad = '  ' * l
    for i, r in enumerate(a[:-1]):
        buf += "%s%s\n" % (pad, r)
    return buf

def quote_if_necessary(s):
    """
    Transforms input data into a quoted string if necessary, determining necessity
    by testing if the input is a dictionary with a single key-value pair in a
    specific format.

    Args:
        s (Union[str, int, float, bool, List[Union[str, int, float, bool]], Dict[str,
            Union[str, int, float, bool]]]): Represented by any valid Python literal
            value, including strings, integers, floats, booleans, lists, or dictionaries.

    Returns:
        str|List[str]: A string that represents a quoted value or a list of strings
        representing quoted values.

    """
    if type(s) is list:
        return [quote_if_necessary(a) for a in s]
    return re.search('{a: (.*)}\n', yaml.dump({'a': s})).group(1)

def prn(n, nm, lvl):
    """
    Generates a formatted string representation of nested data, recursively
    traversing dictionaries and lists, and handling strings, integers, and None
    values appropriately, with indentation and bracketing for clarity.

    Args:
        n (Dict[str | int | list | None, str]): Used to recursively print nested
            dictionaries, lists, strings, and None values, with proper indentation
            and formatting.
        nm (str | int): Used to represent the name of a variable being printed.
            It is either converted to a string representation of an integer if it
            can be parsed as such, or left unchanged if it is a string or cannot
            be parsed as an integer.
        lvl (int): Used to track the current indentation level.

    Returns:
        str: Formatted string representation of input data, suitable for printing,
        with indentation and bracketing as necessary to clearly display nested
        data structures.

    """
    if nm == '*':
        # quote wildcard keys
        nm = "'*'"
    else:
        # quote numeric keys
        try:
            nm_int = int(nm)
        except ValueError:
            pass
        else:
            if str(nm_int) == nm:
                nm = "'%d'" % nm_int
    pad = '  ' * lvl
    if isinstance(n, list):
        return "%s%s: [%s]\n" % (pad, nm, ', '.join(quote_if_necessary(n)))
    elif n is None:
        return "%s%s:\n" % (pad, nm)
    elif isinstance(n, str):
        if len(n.split('\n')) > 1:
            return "%s%s: |\n%s" % (pad, nm, paddify(n, lvl+1))
        else:
            if nm in dont_bracket:
                return "%s%s: %s\n" % (pad, nm, quote_if_necessary(n))
            return "%s%s: [%s]\n" % (pad, nm, ', '.join(quote_if_necessary(n.split())))
    buf = "%s%s:\n" % (pad, nm)
    for a in sorted(n.keys()):
        buf += prn(n[a], a, lvl+1)
    return buf


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cleans a rosdep YAML file to a correct format')
    parser.add_argument('infile', help='input rosdep YAML file')
    parser.add_argument('outfile', help='output YAML file to be written')
    args = parser.parse_args()

    with open(args.infile) as f:
        iny = yaml.load(f.read())

    buf = ''
    for a in sorted(iny):
        buf += prn(iny[a], a, 0)

    with io.open(args.outfile, 'wb') as f:
        f.write(buf.encode('utf-8'))
