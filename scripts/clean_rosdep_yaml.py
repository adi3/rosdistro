#!/usr/bin/env python

import yaml
import argparse
import re
import io

dont_bracket = ['uri', 'md5sum']

def paddify(s, l):
    """
    Indents each line of input text except the last one by a specified level,
    determined by the `l` parameter, resulting in a formatted text with a consistent
    indentation.

    Args:
        s (str): Containing a string that represents a text with newline characters
            (`\n`) separating different lines.
        l (int): Used to specify the number of spaces for padding in each line.

    Returns:
        str: A string containing the original lines of the input string `s`, each
        indented with `l` levels of spaces.

    """
    a = s.split('\n')
    buf = ''
    pad = '  ' * l
    for i, r in enumerate(a[:-1]):
        buf += "%s%s\n" % (pad, r)
    return buf

def quote_if_necessary(s):
    """
    Converts a given value into a quoted string if it contains special characters,
    but only if it is a string. For lists, it recursively applies the conversion
    to each element.

    Args:
        s (str | int | float | bool | List[str | int | float | bool] | Dict[str,
            str | int | float | bool]): Interpreted as a value that may need
            quotation in a YAML dump.

    Returns:
        str|List[str]: A string if the input is a scalar value, or a list of strings
        if the input is a list of scalar values.

    """
    if type(s) is list:
        return [quote_if_necessary(a) for a in s]
    return re.search('{a: (.*)}\n', yaml.dump({'a': s})).group(1)

def prn(n, nm, lvl):
    """
    Recursively prints the contents of nested data structures in a formatted and
    indented manner. It handles various data types, including lists, dictionaries,
    integers, strings, and None, and it quotes strings as necessary.

    Args:
        n (Dict[str | int | list | dict | None]): Represented as a nested data
            structure, which can be a dictionary, a list, a string, an integer,
            or None.
        nm (str | int): Formatted according to its type. If `nm` is a single
            character '*', it is converted to "'*'. Otherwise, if `nm` is an
            integer, it is converted to a string representation.
        lvl (int): Used to track the current indentation level within the function's
            recursive calls.

    Returns:
        str: A formatted string representation of the input data, indented according
        to the specified level (lvl), with key-value pairs recursively nested under
        their respective keys.

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
