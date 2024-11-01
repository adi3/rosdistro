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
    Checks a given text buffer for lines with trailing spaces and prints an error
    message for each occurrence. It returns `False` if any trailing spaces are
    found, indicating the buffer is not clean.

    Args:
        buf (str): Representing the input buffer to be checked for trailing spaces.

    Returns:
        bool: True if all lines in the input buffer `buf` do not have trailing
        spaces, and False otherwise.

    """
    clean = True
    for i, l in enumerate(buf.split('\n')):
        if re.search(r' $', l) is not None:
            print_err("trailing space line %u" % (i+1))
            clean = False
    return clean


def generic_parser(buf, cb):
    """
    Parses a string buffer, iterating line by line, and applies a callback function
    to each line based on its indentation level and content, returning a boolean
    indicating whether the parsing was successful.

    Args:
        buf (str): A string containing a multiline buffer of text to be parsed.
        cb (Callable[[int, str, Dict[str, int]], bool]): Expected to be a callback
            function that processes each line of the input buffer and returns a
            boolean indicating whether the line has been successfully processed.

    Returns:
        bool: True if the parsing is successful and False otherwise, indicating
        whether the buffer was successfully parsed without any errors.

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
    Parses a buffer of text to check for correct indentation levels, reporting
    errors for lines with invalid or excessive indentation.

    Args:
        buf (str): Passed to the `generic_parser` function.

    Returns:
        bool: Either True, indicating that the indentation is correct, or False,
        indicating that an error has been found.

    """
    ilen = len(indent_atom)

    def fun(i, l, o):
        """
        Checks indentation levels in a document. It ensures that a line's indentation
        level is consistent with the previous line's level, preventing excessive
        indentation or invalid indentation levels.

        Args:
            i (int): Representing the current line number of the input being processed.
            l (Dict[str, any]): Used as a dictionary to access the values 's' and
                'lvl' with the keys 's' and 'lvl' respectively.
            o (Dict[str, int]): Used to access specific key-value pairs, specifically
                's' and 'lvl', where 's' represents indentation level and 'lvl'
                represents the current level.

        Returns:
            bool|None: Either `True` if the input line is correctly indented
            according to the given level, or `False` if it is not. If an error
            occurs, `None` is not returned but instead, the function prints an
            error message and returns `False`.

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
    Validates the presence of square brackets around a list in a given buffer of
    text, excluding certain exceptions, and returns a generic parser result.

    Args:
        buf (str): Passed to the `generic_parser` function.

    Returns:
        bool: True if all lines in the input buffer pass the validation check and
        false otherwise.

    """
    excepts = ['uri', 'md5sum']

    def fun(i, l, o):
        """
        Checks if a line of code matches a specific pattern. It validates whether
        the line contains a list not enclosed in square brackets and prints an
        error message if it does, returning `False`. Otherwise, it returns `True`.

        Args:
            i (int): Used to index a line number in a file.
            l (str): Matched against a regular expression r'^(?:' + indent_atom +
                r')*([^:]*):\s*(\w.*)$'.
            o (None): Unused in the given function.

        Returns:
            bool: True if the input line matches the specified pattern and is not
            in the `excepts` list, or if the matched value is 'null'. Otherwise,
            it returns False.

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
    Validates the order of items in a list within a YAML file. It checks each item
    against the previous one, ensuring they are sorted alphabetically, and reports
    any discrepancies.

    Args:
        buf (str): Passed to the `generic_parser` function.

    Returns:
        bool: Either True if all lines in the buffer are in alphabetical order or
        False if any line is out of order.

    """
    def fun(i, l, o):
        """
        Checks a YAML-formatted list for alphabetical order, tracking indentation
        levels. It iterates through lines, parsing items with regular expressions
        and comparing them to previous items at the same level, reporting errors
        if the list is not in order.

        Args:
            i (int): Used to represent the current line number in the input data.
                It is referenced in the error message "line %d" and "line %u".
            l (str): Interpreted as a line of text. It is searched for patterns
                using regular expressions to determine its validity and content.
            o (Dict[str, str]): Named `lvl` within the function, indicating it
                contains a level value.

        Returns:
            bool|str: Either `True` if the input line is valid, or `False` if it's
            not in alphabetical order, or a string describing the error if the
            input line starts with a question mark.

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
            item = yaml.load(m.groups()[0])
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
    Validates the contents of a YAML file by checking for various formatting issues
    and errors, including trailing spaces, incorrect indentation, non-bracket
    package lists, and item order, before building a dictionary from the file.

    Args:
        fname (str): Required, representing the filename of a file that will be
            opened and processed by the function.

    Returns:
        bool: True if the file contents pass all checks and False otherwise.

    """
    with open(fname) as f:
        buf = f.read()

    def my_assert(val):
        """
        Checks a given value. If the value is False, it sets a class attribute
        `clean` of the `my_assert` function to False, indicating a failure or an
        error condition.

        Args:
            val (bool): Used to check the validity of a condition. It seems to be
                a custom assertion function that sets a global variable `my_assert.clean`
                to `False` if the condition is not met.

        """
        if not val:
            my_assert.clean = False
    my_assert.clean = True

    # here be tests.
    ydict = None
    try:
        ydict = yaml.load(buf)
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
        ydict = yaml.load(buf)

        # ensure that values don't contain whitespaces
        whitespace_whitelist = ["el capitan", "mountain lion"]

        def walk(node):
            """
            Traverses a nested data structure recursively, checking for whitespaces
            in string nodes that are not in a whitelist and triggering an error
            if such a string is found.

            Args:
                node (Union[Dict[str, Any], List[Any], str]): Represented as a
                    value in a graph-like data structure. It can be a dictionary,
                    a list, or a string, and is traversed recursively by the `walk`
                    function.

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
