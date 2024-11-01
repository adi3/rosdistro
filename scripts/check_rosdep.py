#!/usr/bin/env python

from __future__ import print_function

import re
import yaml
import argparse
import sys

indent_atom = '  '

# pretty - A miniature library that provides a Python print and stdout
# wrapper that makes colored terminal text easier to use (eg. without
# having to mess around with ANSI escape sequences). This code is public
# domain - there is no license except that you must leave this header.
#
# Copyright (C) 2008 Brian Nez <thedude at bri1 dot com>
#
# With modifications
#           (C) 2013 Paul M <pmathieu@willowgarage.com>

codeCodes = {
    'black':     '0;30',     'bright gray':   '0;37',
    'blue':      '0;34',     'white':         '1;37',
    'green':     '0;32',     'bright blue':   '1;34',
    'cyan':      '0;36',     'bright green':  '1;32',
    'red':       '0;31',     'bright cyan':   '1;36',
    'purple':    '0;35',     'bright red':    '1;31',
    'yellow':    '0;33',     'bright purple': '1;35',
    'dark gray': '1;30',     'bright yellow': '1;33',
    'normal':    '0'
}


def printc(text, color):
    """Print in color."""
    if sys.stdout.isatty():
        print("\033["+codeCodes[color]+"m"+text+"\033[0m")
    else:
        print(text)


def print_test(msg):
    printc(msg, 'yellow')


def print_err(msg):
    printc('  ERR: ' + msg, 'red')


def no_trailing_spaces(buf):
    """
    Checks each line in a given string buffer for trailing spaces. If any are
    found, it prints an error message indicating the line number and returns
    `False`, indicating the buffer is not clean. Otherwise, it returns `True`.

    Args:
        buf (str): Containing a string that represents a buffer of text, typically
            a multi-line string.

    Returns:
        bool: True if no lines in the input buffer have trailing spaces, and False
        otherwise, indicating the presence of at least one line with trailing spaces.

    """
    clean = True
    for i, l in enumerate(buf.split('\n')):
        if re.search(r' $', l) is not None:
            print_err("trailing space line %u" % (i+1))
            clean = False
    return clean


def generic_parser(buf, cb):
    """
    Iterates over lines in a buffer, applies a callback function to each non-empty
    line, and returns a boolean indicating whether the parsing was clean or not.
    It handles indentation and string blocks, skipping lines that start with '#'
    or contain certain characters.

    Args:
        buf (str): A string containing a block of text that is to be parsed.
        cb (Callable[[int, str, Dict[str, int]], bool]): Expected to return a
            boolean value indicating whether the parsing of the given line should
            be considered clean.

    Returns:
        bool: True if parsing is successful and False otherwise.

    """
    ilen = len(indent_atom)
    stringblock = False
    strlvl = 0
    lvl = 0
    clean = True

    for i, l in enumerate(buf.split('\n')):
        if l == '':
            continue
        if re.search(r'^\s*#', l) is not None:
            continue
        try:
            s = re.search(r'(?!' + indent_atom + ')[^\s]', l).start()
        except:
            print_err("line %u: %s" % (i, l))
            raise
        if stringblock:
            if int(s / ilen) > strlvl:
                continue
            stringblock = False
        lvl = int(s / ilen)
        opts = {'lvl': lvl, 's': s}
        if not cb(i, l, opts):
            clean = False
        if re.search(r'\|$|\?$|^\s*\?', l) is not None:
            stringblock = True
            strlvl = lvl
    return clean


def correct_indent(buf):
    """
    Validates the indentation levels in a given buffer of text. It checks if the
    indentation at each line is a multiple of a specified length and if the
    indentation level does not exceed the previous level by more than one.

    Args:
        buf (str): Being passed to the `generic_parser` function, which is likely
            to parse the string for indentation errors.

    Returns:
        bool: Either True if the parsing is successful or False otherwise.

    """
    ilen = len(indent_atom)

    def fun(i, l, o):
        """
        Checks indentation levels in code. It verifies that each line's indentation
        level is valid and not too deep, comparing the current level with the
        previous one.

        Args:
            i (int): Used to represent the current line number being processed,
                used in error messages.
            l (Dict[str, int]): Used as the value of the key 'l' in the function
                `fun`.
            o (Dict[str, int]): Used to access two integer values: `s` and `lvl`.

        Returns:
            bool|None: Returned as True when the input is valid, indicating no
            error. It returns False when an error occurs, such as invalid indentation
            level or too much indentation.

        """
        s = o['s']
        olvl = fun.lvl
        lvl = o['lvl']
        fun.lvl = lvl
        if s % ilen > 0:
            print_err("invalid indentation level line %u: %u" % (i+1, s))
            return False
        if lvl > olvl + 1:
            print_err("too much indentation line %u" % (i+1))
            return False
        return True
    fun.lvl = 0
    return generic_parser(buf, fun)


def check_brackets(buf):
    """
    Checks if each line in a buffer `buf` contains a list enclosed in square
    brackets and not in `excepts` list, and if the list is not empty. It uses a
    regular expression to parse each line and a callback function to print error
    messages if necessary.

    Args:
        buf (str): Passed to the `generic_parser` function, which is not shown in
            the provided code.

    Returns:
        bool: The result of `generic_parser(buf, fun)`, where `generic_parser` is
        assumed to return a boolean value.

    """
    excepts = ['uri', 'md5sum']

    def fun(i, l, o):
        """
        Checks if a line of code is in the correct format and does not contain
        certain exceptions. It uses regular expressions to match the line and
        checks for the presence of a null value or an unsupported exception.

        Args:
            i (int): Used as a line number for error reporting purposes, specifically
                in the `print_err` function where it is used to display the line
                number where an error occurs.
            l (str): Matched against a regular expression pattern to validate its
                format.
            o (None): Unused in the provided function.

        Returns:
            bool: True if the input line matches the expected pattern and is not
            'null', False otherwise.

        """
        m = re.match(r'^(?:' + indent_atom + r')*([^:]*):\s*(\w.*)$', l)
        if m is not None and m.groups()[0] not in excepts:
            if m.groups()[1] == 'null':
                return True
            print_err("list not in square brackets line %u" % (i+1))
            return False
        return True
    return generic_parser(buf, fun)


def check_order(buf):
    """
    Validates the order of items in a list within a YAML file, ensuring they are
    in alphabetical order and correctly formatted according to a specific pattern.

    Args:
        buf (str): The input buffer to be parsed, containing a sequence of lines
            that may include indentation, question marks, and YAML-formatted items.

    Returns:
        bool: True if all lines in the input buffer are in alphabetical order and
        False otherwise.

    """
    def fun(i, l, o):
        """
        Enforces alphabetical order in a list by parsing input lines, comparing
        each item with its previous one, and printing an error message if a line
        is out of order.

        Args:
            i (int): Used to specify the line number in a file being processed,
                used in error messages and for debugging purposes.
            l (str): Used as a line of text. It appears to be a line from a
                configuration file, possibly a YAML file, and is processed by
                regular expressions to extract a key-value pair.
            o (Dict[str, int]): Named `lvl`, which represents the current level
                in a nested list or dictionary.

        Returns:
            bool: True if the input line is in alphabetical order and False otherwise.

        """
        lvl = o['lvl']
        st = fun.namestack
        while len(st) > lvl + 1:
            st.pop()
        if len(st) < lvl + 1:
            st.append('')
        if re.search(r'^\s*\?', l) is not None:
            return True
        m = re.match(r'^(?:' + indent_atom + r')*([^:]*):.*$', l)
        prev = st[lvl]
        try:
            # parse as yaml to parse `"foo bar"` as string 'foo bar' not string '"foo bar"'
            item = yaml.safe_load(m.groups()[0])
        except:
            print('woops line %d' % i)
            raise
        st[lvl] = item
        if item < prev:
            print_err("list out of alphabetical order line %u.  '%s' should come before '%s'" % ((i+1), item, prev))
            return False
        return True
    fun.namestack = ['']
    return generic_parser(buf, fun)


def main(fname):
    """
    Validates YAML files by checking for specific formatting and content issues,
    including trailing spaces, indentation, package lists, item order, and whitespace
    in string values. It returns `True` if the file is valid, and `False` otherwise.

    Args:
        fname (str): Used to specify the name of a file that will be opened for reading.

    Returns:
        bool: True if the input file passes all checks and False otherwise.

    """
    with open(fname) as f:
        buf = f.read()

    def my_assert(val):
        """
        Checks the input `val` for truthiness. If `val` is falsey, it sets the
        `clean` attribute of the function itself to `False`. This is a custom
        assertion mechanism.

        Args:
            val (bool): Checked to determine if it represents a truthy value.

        """
        if not val:
            my_assert.clean = False
    my_assert.clean = True

    # here be tests.
    ydict = None
    try:
        ydict = yaml.safe_load(buf)
    except Exception:
        pass
    if ydict != {}:
        print_test("checking for trailing spaces...")
        my_assert(no_trailing_spaces(buf))
        print_test("checking for incorrect indentation...")
        my_assert(correct_indent(buf))
        print_test("checking for non-bracket package lists...")
        my_assert(check_brackets(buf))
        print_test("checking for item order...")
        my_assert(check_order(buf))
        print_test("building yaml dict...")
    else:
        print_test("skipping file with empty dict contents...")
    try:
        ydict = yaml.safe_load(buf)

        # ensure that values don't contain whitespaces
        whitespace_whitelist = ["el capitan", "mountain lion"]

        def walk(node):
            """
            Traverses a nested data structure recursively, checking for whitespace
            characters in strings, and raises an error if a string with whitespace
            is found and not whitelisted.

            Args:
                node (str | dict | list): Represented as a value in a recursive
                    tree structure, where each node can be a dictionary, a list,
                    or a string.

            """
            if isinstance(node, dict):
                for key, value in node.items():
                    walk(key)
                    walk(value)
            if isinstance(node, list):
                for value in node:
                    walk(value)
            if isinstance(node, str) and re.search(r'\s', node) and node not in whitespace_whitelist:
                    print_err("value '%s' must not contain whitespaces" % node)
                    my_assert(False)
        walk(ydict)

    except Exception as e:
        print_err("could not build the dict: %s" % (str(e)))
        my_assert(False)

    if not my_assert.clean:
        printc("there were errors, please correct the file", 'bright red')
        return False
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Checks whether yaml syntax corresponds to ROS rules')
    parser.add_argument('infile', help='input rosdep YAML file')
    args = parser.parse_args()

    if not main(args.infile):
        sys.exit(1)
