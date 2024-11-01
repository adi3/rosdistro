#!/usr/bin/env python

import yaml
import argparse
import re
import io

dont_bracket = ['uri', 'md5sum']

def paddify(s, l):
    """
    Indentifies each line of input string `s` except the last one, and pads it
    with a specified number of spaces `l` to create a formatted string with
    consistent indentation.

    Args:
        s (str): Interpreted as a string containing a text with newline characters.
        l (int): Used to specify the number of spaces to use for padding each line.

    Returns:
        str: A string containing the input lines padded with spaces to a specified
        indentation level.

    """
    a = s.split('\n')
    buf = ''
    pad = '  ' * l
    for i, r in enumerate(a[:-1]):
        buf += "%s%s\n" % (pad, r)
    return buf

def quote_if_necessary(s):
    """
    Checks if the input is a list and recursively calls itself for each item in
    the list. If the input is a single value, it uses regular expressions to find
    any embedded YAML code and returns the unquoted value within.

    Args:
        s (Union[str, int, float, bool, List[Union[str, int, float, bool]], Dict[str,
            Union[str, int, float, bool]]]): Represented as an argument to be
            processed by the function, which may contain various data types,
            including strings, integers, floats, booleans, lists, and dictionaries.

    Returns:
        str|List[str]: A string if the input is a single non-list value, and a
        list of strings if the input is a list.

    """
    if type(s) is list:
        return [quote_if_necessary(a) for a in s]
    return re.search('{a: (.*)}\n', yaml.dump({'a': s})).group(1)

def prn(n, nm, lvl):
    """
    Recursively prints the contents of nested dictionaries, lists, and strings,
    with proper indentation and formatting, handling various data types and edge
    cases.

    Args:
        n (Dict[str, object | list | dict]): Used to recursively traverse a nested
            data structure, which can be a dictionary, a list, or a string.
        nm (str | int): Used to represent a name for the value being printed. It
            can be an asterisk (*) to indicate the root of the object being printed,
            or an integer that is converted to a string with quotes.
        lvl (int): Used to track the current indentation level, which is used to
            format the output. It is incremented for each recursive call to `prn`
            to maintain a consistent indentation.

    Returns:
        str: Formatted string representation of a nested data structure. It handles
        lists, dictionaries, strings, and null values, applying proper indentation
        and formatting to make the output readable.

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
