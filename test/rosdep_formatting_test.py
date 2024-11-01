#!/usr/bin/env python

import os

from scripts.check_rosdep import main as check_rosdep

from .fold_block import Fold


def test():
    """
    Checks all YAML files in the 'rosdep' directory for issues using the `check_rosdep`
    function. It skips non-YAML files and reports any errors found, providing a
    cleanup option if the check fails.

    """
    files = os.listdir('rosdep')

    with Fold() as fold:
        print("""Running 'scripts/check_rosdep.py' on all '*.yaml' in the 'rosdep' directory.
If this fails you can run 'scripts/clean_rosdep_yaml.py' to help cleanup.
""")

        for f in sorted(files):
            fname = os.path.join('rosdep', f)
            if not f.endswith('.yaml'):
                print("Skipping rosdep check of file %s" % fname)
                continue
            print("Checking rosdep file: %s" % fname)
            assert check_rosdep(fname), fold.get_message()
