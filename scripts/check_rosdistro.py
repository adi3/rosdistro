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
    Checks a given string buffer for lines containing trailing spaces. It iterates
    over each line, searches for trailing spaces using a regular expression, and
    if found, prints an error message and sets the `clean` flag to `False`.

    Args:
        buf (str): Containing a string of text that represents a buffer of lines,
            where each line is separated by a newline character.

    Returns:
        bool: Indicating whether the input buffer contains any lines with trailing
        spaces.

    """
    clean = True
    for i, l in enumerate(buf.split('\n')):
        if re.search(r' $', l) is not None:
            print_err("trailing space line %u" % (i+1))
            clean = False
    return clean

def generic_parser(buf, cb):
    """
    Iterates over a buffer of lines, applying a callback function to each line
    based on its indentation level and content, and returns a boolean indicating
    whether the parsing was successful.

    Args:
        buf (str): A string containing a block of text, split into lines, which
            is to be parsed by the function.
        cb (Callable[[int, str, Dict[str, int]], bool]): Called a callback function.
            It is a function that takes three arguments: the line number `i`, the
            line `l`, and a dictionary `opts` containing the level `lvl` and start
            position `s` of the line. The callback function returns a boolean value
            indicating whether the line is processed successfully.

    Returns:
        bool: True if all lines in the input buffer pass the callback function's
        validation, and False otherwise.

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
    Validates the indentation of lines in a buffer by comparing each line's
    indentation level with the previous one, reporting errors for invalid or
    excessive indentation.

    Args:
        buf (str | bytes): A string or bytes object to be parsed.

    Returns:
        bool: True if the input buffer contains valid indentation levels and False
        otherwise.

    """
    ilen = len(indent_atom)
    def fun(i, l, o):
        """
        Validates indentation levels in a code snippet. It checks if the current
        indentation level is a multiple of a certain value (`ilen`) and if it
        exceeds the previous level by more than one. It prints error messages and
        returns `False` if any conditions are not met.

        Args:
            i (int): Representing the current line number being processed.
            l (Dict[str, int]): Used as a dictionary to store object values, with
                keys like 's' and 'lvl'.
            o (Dict[str, int | str]): Passed as a dictionary to the function,
                likely representing an object or options.

        Returns:
            bool|None: Translated to a more explicit type, it is `bool` if an error
            occurs, and `None` otherwise.

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
    Parses a buffer of text using a generic parser and checks each line to ensure
    that any list not in square brackets is printed as an error and returns False.

    Args:
        buf (str): Passed to the `generic_parser` function, which is not shown in
            the given code.

    Returns:
        bool: Returned by the `generic_parser` function, which is called with the
        `fun` function as its argument.

    """
    excepts = ['uri', 'md5sum']
    def fun(i, l, o):
        """
        Validates a line of code by checking if it contains a list not enclosed
        in square brackets. If such a line is found, it prints an error message
        and returns False; otherwise, it returns True.

        Args:
            i (int): Used as an index to reference a line number, where the function
                prints an error message if the line is not in square brackets. The
                line number is incremented by 1 before being used in the error message.
            l (str): Matched against a regular expression pattern to validate its
                structure and content.
            o (object): Unused in the provided function, suggesting it may be a
                leftover or intended for future use.

        Returns:
            bool: `True` if the input line matches certain conditions and `False`
            otherwise.

        """
        m = re.match(r'^(?:' + indent_atom + r')*([^:]*):\s*(\w.*)$', l)
        if m is not None and m.groups()[0] not in excepts:
            print_err("list not in square brackets line %u" % (i+1))
            return False
        return True
    return generic_parser(buf, fun)

def check_order(buf):
    """
    Parses a buffer of lines and checks if the items in a list are in alphabetical
    order, reporting any out-of-order items. It uses a recursive approach to track
    the current list level and its items.

    Args:
        buf (str): Passed to the `generic_parser` function, which is not shown in
            the code snippet.

    Returns:
        bool: Either True when the input list is in alphabetical order or False
        when it is not.

    """
    def fun(i, l, o):
        """
        Enforces alphabetical order in a list by iterating through a stack of items
        at a specified level, updating the current item and checking if it is in
        order.

        Args:
            i (int): Used as a line number in error messages.
            l (str): Checked for lines starting with whitespace followed by a
                question mark using a regular expression.
            o (Dict[str, int]): Extracted as a dictionary with a single key-value
                pair, where the key is 'lvl' and the value is the level of indentation.

        Returns:
            bool: True if the input list is in alphabetical order or contains a
            line that starts with a question mark, and False otherwise.

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
    Validates a YAML file by checking its contents and structure. It loads the
    YAML into a dictionary, checks for errors such as trailing spaces, incorrect
    indentation, and item order, and returns `True` if the file is valid or `False`
    otherwise.

    Args:
        fname (str): Designated to hold the name of a file to be read by the function.

    Returns:
        bool: `True` if the file is valid and `False` if there are errors.

    """
    with open(fname) as f:
        buf = f.read()

    def my_assert(val):
        """
        Checks the input value `val`. If `val` is False, it sets a global variable
        `my_assert.clean` to False, effectively indicating a failed assertion.

        Args:
            val (bool): Evaluated in a conditional statement to determine whether
                the function should set `my_assert.clean` to `False`.

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


