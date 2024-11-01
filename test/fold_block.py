import os

next_block_id = 1


class Fold(object):

    """
    Manages block-level logging for Travis CI, a continuous integration platform.
    It generates a unique block ID for each fold, prints fold start and end messages
    if running on Travis CI, and provides a way to include additional messages in
    the fold.

    Attributes:
        block_id (int): Assigned a unique value on each instance creation,
            incrementing a global variable `next_block_id` by 1.

    """
    def __init__(self):
        """
        Assigns a unique identifier to each instance of the Fold class. It retrieves
        the current global next_block_id, assigns it to the instance's block_id,
        and then increments the global next_block_id for the next instance.

        """
        global next_block_id
        self.block_id = next_block_id
        next_block_id += 1

    def get_message(self, msg=''):
        """
        Adds a message to be returned, which includes a reference to a folded block
        above, when the environment variable 'TRAVIS' is set to 'true'.

        Args:
            msg (str): Optional, defaulting to an empty string. It appears to be
                a message that can be appended to with additional information.

        Returns:
            str|None: A string containing additional information about a test
            failure, or an empty string if no additional information is needed.

        """
        if os.environ.get('TRAVIS') == 'true':
            if msg:
                msg += ', '
            msg += "see folded block '%s' above for details" % self.get_block_name()
        return msg

    def get_block_name(self):
        return 'block%d' % self.block_id

    def __enter__(self):
        """
        Enables the class to be used as a context manager, returning the instance
        when entering a with statement block. It also prints a specific message
        if the environment variable TRAVIS is set to true.

        Returns:
            self: An instance of the class it is called on.

        """
        if os.environ.get('TRAVIS') == 'true':
            print('travis_fold:start:%s' % self.get_block_name())
        return self

    def __exit__(self, type, value, traceback):
        """
        Handles the exit of a context manager, specifically printing a message to
        indicate the end of a block when the code is running on Travis CI.

        Args:
            type (ExceptionType): Indicated as the type of exception that occurred,
                if any, during the execution of the code within the `with` block.
            value (Exception): Passed when an exception occurs within the `with`
                block.
            traceback (Traceback
                is a type that is typically a string, but can be a ): Provide a
                more detailed description of the `traceback` parameter.
                The `traceback` parameter is an optional parameter that contains
                exception information.
                It is a string that includes information about the sequence of
                function calls that led to the exception.

        """
        if os.environ.get('TRAVIS') == 'true':
            print('travis_fold:end:%s' % self.get_block_name())
