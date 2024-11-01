#!/usr/bin/env python
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
    'black':    '0;30',     'bright gray':  '0;37',
    'blue':     '0;34',     'white':        '1;37',
    'green':    '0;32',     'bright blue':  '1;34',
    'cyan':     '0;36',     'bright green': '1;32',
    'red':      '0;31',     'bright cyan':  '1;36',
    'purple':   '0;35',     'bright red':   '1;31',
    'yellow':   '0;33',     'bright purple':'1;35',
    'dark gray':'1;30',     'bright yellow':'1;33',
    'normal':   '0'
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
    Checks a string for lines containing trailing spaces, prints an error message
    for each occurrence, and returns `False` if any lines contain trailing spaces,
    or `True` if the input string is clean.

    Args:
        buf (str): A string representing a buffer of text, which is split into
            lines for processing.

    Returns:
        bool: True if no lines in the buffer have trailing spaces, False otherwise.

    """
    clean = True
    for i, l in enumerate(buf.split('\n')):
        if re.search(r' $', l) is not None:
            print_err("trailing space line %u" % (i+1))
            clean = False
    return clean

def generic_parser(buf, cb):
    """
    Iterates over a text buffer line by line, applying a callback function to each
    line based on its indentation level and content. It handles indentation,
    strings, and errors, returning a boolean indicating whether the parsing process
    was clean.

    Args:
        buf (str): Used to represent a string containing multiple lines of text.
            It appears to be the input data to be parsed.
        cb (Callable[[int, str, Dict[str, int]], bool]): Called a callback function.
            It takes three arguments: the line number `i`, the line content `l`,
            and a dictionary `opts` containing the level `lvl` and the start
            position `s` of the current line. It returns a boolean value indicating
            whether the line should be processed.

    Returns:
        bool: True if all lines in the buffer pass the callback test, and False otherwise.

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
            s = re.search(r'(?!' + indent_atom + ')(\w|\?)', l).start()
        except:
            print_err("line %u: %s" % (i, l))
            raise
        if stringblock:
            if int(s / ilen) > strlvl:
                continue
            stringblock = False
        lvl = s / ilen
        opts = {'lvl': lvl, 's': s}
        if not cb(i, l, opts):
            clean = False
        if re.search(r'\|$|\?$|^\s*\?', l) is not None:
            stringblock = True
            strlvl = lvl
    return clean


def correct_indent(buf):
    """
    Checks a given buffer for correct indentation levels. It returns True if the
    indentation is correct, False otherwise. It also prints error messages when
    invalid indentation is found.

    Args:
        buf (str): Used as input to the `generic_parser` function.

    Returns:
        bool: Either True or False.

    """
    ilen = len(indent_atom)
    def fun(i, l, o):
        """
        Checks indentation levels in a code snippet. It compares the current
        indentation level with the previous one, ensuring it is not too much and
        is a multiple of the indentation length. It also checks for invalid
        indentation levels and reports errors if necessary.

        Args:
            i (int): Used as a line number, indicating the current line being
                processed in a sequence of lines.
            l (List[str]): Used as a context for the function to perform indentation
                level checks.
            o (Dict[str, int]): Represented as a Python dictionary containing at
                least two key-value pairs: 's' and 'lvl'. The 's' key maps to an
                integer representing the current indentation level and the 'lvl'
                key maps to an integer representing the current level.

        Returns:
            bool: True when the input is valid and False when the input is invalid.

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
    Parses a string buffer and checks if each line is in square brackets. It returns
    False if a line is not in square brackets and its key is not in the 'excepts'
    list, otherwise it returns True.

    Args:
        buf (str): Passed to the `generic_parser` function, which is not defined
            within this snippet.

    Returns:
        bool: The result of the `generic_parser` function, indicating whether the
        input buffer `buf` is valid according to the specified parsing rules.

    """
    excepts = ['uri', 'md5sum']
    def fun(i, l, o):
        """
        Checks if a given line matches a specific pattern and if its first group
        is not in a predefined list of exceptions. It returns `False` if the line
        is not in square brackets and prints an error message. Otherwise, it returns
        `True`.

        Args:
            i (int): Used as a line number for error reporting purposes.
            l (str): Matched against a regular expression. It appears to be a line
                of text that is being parsed, likely from a configuration file or
                similar source.
            o (Any): Unused, as it is not referenced within the function.

        Returns:
            bool: True if the input line matches the specified pattern and is not
            in the excepts list, and False otherwise.

        """
        m = re.match(r'^(?:' + indent_atom + r')*([^:]*):\s*(\w.*)$', l)
        if m is not None and m.groups()[0] not in excepts:
            print_err("list not in square brackets line %u" % (i+1))
            return False
        return True
    return generic_parser(buf, fun)

def check_order(buf):
    """
    Validates the order of items in a list within a configuration file. It checks
    each line against the previous line, ensuring the items are in alphabetical
    order and reports errors if not.

    Args:
        buf (str): Passed to the `generic_parser` function, which is not shown in
            the code snippet.

    Returns:
        bool: Either True indicating that the input list is in alphabetical order
        or False indicating that it is not.

    """
    def fun(i, l, o):
        """
        Checks the input list against a set of rules: it verifies that each line
        starts with a question mark, is alphabetically ordered, and maintains a
        stack-based indentation structure consistent with a specified level.

        Args:
            i (int): Used as a line number, indicating the current line being processed.
            l (str): Interpreted as a line of text. It appears to be a line from
                a configuration or data file, possibly with indentation.
            o (Dict[str, int]): Used to access the value of 'lvl' which is likely
                used to track the current indentation level.

        Returns:
            bool: True if the input line is in alphabetical order and does not
            contain a question mark, False otherwise.

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
            item = m.groups()[0]
        except:
            print('woops line %d' % i)
            raise
        st[lvl] = item
        if item < prev:
            print_err("list out of alphabetical order line %u" % (i+1))
            return False
        return True
    fun.namestack = ['']
    return generic_parser(buf, fun)


def main(fname):
    """
    Validates a YAML file by checking for trailing spaces, correct indentation,
    item order, and building a YAML dictionary. It returns True if the file is
    valid and False otherwise, also printing error messages if necessary.

    Args:
        fname (str): A filename that the function reads to process its contents.

    Returns:
        bool: True if the file is valid and False otherwise.

    """
    with open(fname) as f:
        buf = f.read()

    def my_assert(val):
        """
        Sets a global variable `clean` to `False` if its argument `val` is `False`.

        Args:
            val (bool): Checked for its truthiness.

        """
        if not val:
            my_assert.clean = False
    my_assert.clean = True

    try:
        ydict = yaml.load(buf)
    except Exception as e:
        print_err("could not build the dict: %s" % (str(e)))
        my_assert(False)

    if 'release-name' not in ydict and isinstance(ydict, dict) and 'fuerte' not in ydict.keys():
        print_err("The file does not contain a 'release-name'. (Only files for Fuerte and older are supported by this script)")
    else:
        print_test("checking for trailing spaces...")
        my_assert(no_trailing_spaces(buf))
        print_test("checking for incorrect indentation...")
        my_assert(correct_indent(buf))
        print_test("checking for item order...")
        my_assert(check_order(buf))
        print_test("building yaml dict...")

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


