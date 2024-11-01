import os

next_block_id = 1


class Fold(object):

    """
    Manages code folding blocks for testing purposes, primarily on Travis CI. It
    generates unique block IDs and provides methods to get block names, messages,
    and print folding start and end markers when running on Travis CI.

    Attributes:
        block_id (int): Assigned a unique value on each object creation, incrementing
            a global variable `next_block_id`. This ensures that each block has a
            distinct identifier.

    """
    def __init__(self):
        """
        Assigns a unique block ID to each instance of the Fold class, incrementing
        a global variable `next_block_id` to ensure uniqueness.

        """
        global next_block_id
        self.block_id = next_block_id
        next_block_id += 1

    def get_message(self, msg=''):
        """
        Constructs a message based on the environment. If running on Travis CI,
        it appends a default message to the provided message, including a reference
        to the folded block name. Otherwise, it returns the original message.

        Args:
            msg (str): Optional, defaulting to an empty string.

        Returns:
            str|None: A string that may or may not include a message and a reference
            to a folded block, or None if no message is provided and the environment
            variable 'TRAVIS' is not set to 'true'.

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
        Determines if the code is being executed in a Travis CI environment. If
        so, it prints a message indicating the start of a block with a name obtained
        from the `get_block_name` method.

        Returns:
            self: An instance of the class in which the function is defined.

        """
        if os.environ.get('TRAVIS') == 'true':
            print('travis_fold:start:%s' % self.get_block_name())
        return self

    def __exit__(self, type, value, traceback):
        """
        Handles the exit of a context manager, specifically in a Travis CI
        environment. It prints a message to indicate the end of a block, using the
        block name obtained from the `get_block_name` method.

        Args:
            type (ExceptionType): Representing the type of exception that occurred
                during execution of the code block.
            value (Exception): The exception instance that occurred during execution
                of the code block if an exception occurred, otherwise `None`.
            traceback (TracebackType = Optional[types.TracebackType]): Used to
                represent the traceback of an exception if one was raised during
                the execution of the `__enter__` method.

        """
        if os.environ.get('TRAVIS') == 'true':
            print('travis_fold:end:%s' % self.get_block_name())
