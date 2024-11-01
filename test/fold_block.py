import os

next_block_id = 1


class Fold(object):

    """
    Manages a sequence of blocks, assigning a unique ID to each block. It also
    provides methods to get a block's message and name, and to print start and end
    markers for the blocks, specifically designed for Travis CI testing.

    Attributes:
        block_id (int): Incremented by 1 each time a new `Fold` object is created.

    """
    def __init__(self):
        """
        Assigns a unique block identifier to each instance of the Fold class,
        incrementing a global counter `next_block_id` after assignment. This ensures
        that each block has a distinct identifier.

        """
        global next_block_id
        self.block_id = next_block_id
        next_block_id += 1

    def get_message(self, msg=''):
        """
        Constructs and returns a message based on the environment. If running on
        Travis CI, the message includes a reference to a folded block above with
        details. Otherwise, it returns an empty string or the provided message unchanged.

        Args:
            msg (str | None): Initialized with an empty string, allowing the
                function to append additional information to it if needed. It
                defaults to an empty string if not provided.

        Returns:
            str|None: A message string that may contain additional information,
            or None if the function is called without any arguments.

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
        Establishes a context for the Fold object, which includes printing a message
        with the block name if the environment variable 'TRAVIS' is set to 'true'.

        Returns:
            self: An instance of the class containing this method.

        """
        if os.environ.get('TRAVIS') == 'true':
            print('travis_fold:start:%s' % self.get_block_name())
        return self

    def __exit__(self, type, value, traceback):
        """
        Handles the exit of a context manager, printing a specific string to
        indicate the end of a block when running on Travis CI, a continuous
        integration platform.

        Args:
            type (ExceptionType): Passed to the `__exit__` method when it is called.
                It is the type of exception that was raised, if any.
            value (Exception): Represented the exception instance that occurred
                within the context, if any, otherwise None.
            traceback (Traceback): Related to exception handling in Python. It
                contains information about the call stack at the point where an
                exception occurred.

        """
        if os.environ.get('TRAVIS') == 'true':
            print('travis_fold:end:%s' % self.get_block_name())
