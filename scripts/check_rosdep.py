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
    Checks a given buffer of text for lines containing trailing spaces. It iterates
    over each line, uses a regular expression to search for trailing spaces, and
    prints an error message if any are found, returning False to indicate the
    buffer is not clean.

    Args:
        buf (str): Expected to contain a string of text that has been split into
            lines using the newline character (`\n`).

    Returns:
        bool: True if no lines in the input buffer have trailing spaces, and False
        otherwise.

    """
    clean = True
    for i, l in enumerate(buf.split('\n')):
        if re.search(r' $', l) is not None:
            print_err("trailing space line %u" % (i+1))
            clean = False
    return clean


def generic_parser(buf, cb):
    """
    Parses a string buffer line by line, applying a callback function to each line
    and its corresponding indentation level, skipping comments and string blocks.

    Args:
        buf (str): A string containing a buffer of text, typically a file or string
            content to be parsed line by line.
        cb (Callable[[int, str, Dict[str, int]], bool]): Expected to be a callback
            function. It is called with the line number, line content, and a
            dictionary of options, and it must return a boolean indicating whether
            the parsing should continue.

    Returns:
        bool: `True` if all lines in the buffer pass the callback function, and
        `False` otherwise.

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
    Checks the indentation of lines in a given buffer, ensuring that each line's
    indentation level is consistent with the previous line and a specified indentation
    length. It returns a boolean indicating whether the indentation is correct.

    Args:
        buf (str): Passed to the `generic_parser` function.

    Returns:
        bool: The result of the generic_parser function, indicating whether the
        input buffer was parsed successfully or not.

    """
    ilen = len(indent_atom)

    def fun(i, l, o):
        """
        Checks indentation levels in a source code. It verifies that indentation
        levels are consistent and do not exceed a certain threshold, reporting
        errors if these conditions are not met.

        Args:
            i (int): Used to represent the current line number being processed in
                a file or text. It is used in error messages.
            l (Dict[str, int]): Represented as `o` in the function, but it is
                passed in as `l` and is used to access dictionary keys.
            o (Dict[str, int]): Accessed as a dictionary to retrieve two integer
                values: 's' and 'lvl'.

        Returns:
            bool|None: Either `True` if the input parameters are valid, indicating
            that the indentation level is correct, or `False` if the input parameters
            are invalid, indicating that the indentation level is incorrect or inconsistent.

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
    Checks if square brackets are used correctly in lines that are not exceptions.
    It uses a regular expression to match lines and verifies if they contain a
    value other than 'null' in square brackets.

    Args:
        buf (str): Parsed by the `generic_parser` function, which is not shown in
            the code snippet.

    Returns:
        bool: The result of the `generic_parser` function, indicating whether the
        input buffer `buf` is parsed successfully or not.

    """
    excepts = ['uri', 'md5sum']

    def fun(i, l, o):
        """
        Validates a line of code by checking if it matches a specific pattern and
        if its value is not 'null'. It prints an error message if the line is not
        in square brackets and returns True if the line is valid, False otherwise.

        Args:
            i (int): Used as a line number, indicating the current line being
                processed in a list or file.
            l (str): Matched against a regular expression pattern to extract
                information from it.
            o (not defined.): Unused in the `fun` function.

        Returns:
            bool: True if the input line matches the specified pattern and is not
            in the excepts list, and the second group in the match is not 'null',
            otherwise it returns False.

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
    Checks the order of items in a YAML data structure, ensuring they are in
    alphabetical order. It uses a recursive approach, maintaining a stack to track
    the items at each level.

    Args:
        buf (str): Passed to the `generic_parser` function, indicating that it is
            a buffer or a string that needs to be parsed.

    Returns:
        bool: Either `True` if the input buffer is in a valid alphabetical order,
        or `False` if it is not.

    """
    def fun(i, l, o):
        """
        Validates a list of items, ensuring they are in alphabetical order. It
        uses a stack to track the previous item at each level, comparing each new
        item against it.

        Args:
            i (int): Used to identify a line number, which is referenced in the
                error message when the list is out of alphabetical order.
            l (str): Matched against a regular expression pattern to extract a
                key-value pair. The pattern matches one or more leading indented
                lines, followed by a line containing a colon, where the part before
                the colon is captured as a group.
            o (Dict[str, int]): Named `o`. It contains a single key-value pair
                where the key is `'lvl'` and the value is an integer, representing
                the current level.

        Returns:
            bool: Either `True` indicating that the input list is in alphabetical
            order, or `False` indicating that it is not.

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
    Validates the contents of a YAML file. It checks for trailing spaces, correct
    indentation, bracket usage in package lists, item order, and whitespace presence
    in string values, then returns True if the file is valid and False if errors
    are found.

    Args:
        fname (str): Representing the name of the file to be opened and processed
            by the function.

    Returns:
        bool: True if the file contents pass all checks, and False otherwise.

    """
    with open(fname) as f:
        buf = f.read()

    def my_assert(val):
        """
        Defines a custom assertion mechanism that sets a class attribute `clean`
        to `False` when the input `val` is `False`, indicating a failure in the assertion.

        Args:
            val (bool): Checked to determine if it is not True, in which case the
                function continues to execute.

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
            Traverses a nested data structure recursively, checking each value for
            whitespace if it is a string and not in a whitelist. It prints an error
            message and asserts False if a string with whitespace is found.

            Args:
                node (Union[str, dict, list]): Represented by the node parameter,
                    which is an object that can be a string, a dictionary, or a
                    list, indicating the current element being processed in the
                    recursive traversal.

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
