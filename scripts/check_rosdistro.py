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
    Checks each line in a given text buffer for trailing spaces. It prints an error
    message if any line contains trailing spaces and returns `False` to indicate
    the buffer is not clean. Otherwise, it returns `True`.

    Args:
        buf (str): A string containing a buffer of text to be checked for trailing
            spaces.

    Returns:
        bool: True if all lines in the buffer have no trailing spaces, False otherwise.

    """
    clean = True
    for i, l in enumerate(buf.split('\n')):
        if re.search(r' $', l) is not None:
            print_err("trailing space line %u" % (i+1))
            clean = False
    return clean

def generic_parser(buf, cb):
    """
    Iterates through a buffer of text, parsing lines based on indentation and
    specific characters. It calls a callback function for each line, allowing
    customization of line processing. The function returns True if all lines were
    processed successfully, False otherwise.

    Args:
        buf (str): A string containing a buffer of newline-separated lines of text
            that is being parsed.
        cb (Callable[[int, str, Dict[str, int]], bool]): Expected to be a callback
            function that takes three arguments: the line number `i`, the line
            content `l`, and a dictionary `opts` containing the level `lvl` and
            start position `s` of the line. It returns a boolean value indicating
            whether the line is valid.

    Returns:
        bool: True if the parsing is successful and False otherwise, indicating
        whether the input buffer was parsed cleanly.

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
    Validates the indentation of lines in a source code buffer by comparing each
    line's indentation level to the previous level, reporting any inconsistencies.

    Args:
        buf (str): Passed to the `generic_parser` function. It represents a buffer
            containing the source code to be parsed for indentation errors.

    Returns:
        bool: The result of the `generic_parser` function call, indicating whether
        the input buffer was successfully parsed.

    """
    ilen = len(indent_atom)
    def fun(i, l, o):
        """
        Checks indentation levels in a file or text. It compares the current
        indentation level with the previous one, issuing an error if the indentation
        is invalid or excessive, and returns a boolean indicating whether the
        indentation is valid.

        Args:
            i (int): Representing the line number of the code being processed,
                likely used for error reporting purposes.
            l (Dict[str, int]): Used to access dictionary values, specifically the
                key 's' and 'lvl', which store indentation level and level respectively.
            o (Dict[str, int]): Initialized with the key-value pair 's': some_value
                and 'lvl': some_value, where some_value is an integer.

        Returns:
            bool: True if the indentation level of a line of code is valid according
            to the provided rules, False otherwise.

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
    Checks if a given buffer `buf` contains a list not enclosed in square brackets,
    except for specific cases. It uses a regular expression to match the list and
    prints an error message if the condition is not met.

    Args:
        buf (str): Passed to the `generic_parser` function.

    Returns:
        bool: True if the parsing of the input buffer is successful and false
        otherwise, based on the result of the `generic_parser` function.

    """
    excepts = ['uri', 'md5sum']
    def fun(i, l, o):
        """
        Checks if a line of input matches a specific format and is not in a list
        of excluded items. It returns `True` if the line is valid, `False` otherwise,
        and prints an error message if the line is not in square brackets.

        Args:
            i (int): Used to represent the current line number being processed in
                the list.
            l (str): Matched against a regular expression to extract a key-value
                pair from a line of text.
            o (None): Unused in the provided function.

        Returns:
            bool: True if the input conditions are met and False otherwise,
            specifically when a list is not enclosed in square brackets.

        """
        m = re.match(r'^(?:' + indent_atom + r')*([^:]*):\s*(\w.*)$', l)
        if m is not None and m.groups()[0] not in excepts:
            print_err("list not in square brackets line %u" % (i+1))
            return False
        return True
    return generic_parser(buf, fun)

def check_order(buf):
    """
    Checks the order of items in a list that is being parsed and formatted. It
    verifies that each item is alphabetically greater than or equal to the previous
    item.

    Args:
        buf (str): Referenced by the `generic_parser` function, suggesting it is
            a buffer or a string containing input data to be parsed.

    Returns:
        bool: True if the input list is in alphabetical order and False otherwise.

    """
    def fun(i, l, o):
        """
        Validates the input line `l` against a list's ordering and indentation,
        based on a stack of items stored in `fun.namestack`. It checks for
        alphabetical order and correct indentation, printing error messages if necessary.

        Args:
            i (int): Used to track the current line number, which is referenced
                when printing error messages.
            l (str): Used as input to regular expressions for pattern matching.
            o (Dict[str, int]): Named `o`. It contains a key-value pair where the
                key is `'lvl'` and the value is an integer, which represents a level.

        Returns:
            bool: True if the input line is valid and False otherwise, indicating
            that the line is either a valid question or not in alphabetical order
            with the previous item.

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
    Validates a YAML file by checking for trailing spaces, incorrect indentation,
    item order, and building a YAML dictionary. It uses a custom assertion function
    to track errors and returns True if the file is valid, False otherwise.

    Args:
        fname (str): Required, representing the name of a file to be processed by
            the function.

    Returns:
        bool: `True` if the file passed all checks, and `False` otherwise.

    """
    with open(fname) as f:
        buf = f.read()

    def my_assert(val):
        """
        Checks a given value and sets a global variable `clean` to `False` if the
        value is falsey. This function appears to be a custom assertion mechanism
        that can be used to track the validity of values in a program.

        Args:
            val (bool): Checked for falseness in the function's conditional statement.

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


