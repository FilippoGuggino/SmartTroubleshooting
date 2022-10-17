"""
Utility functions for testing.

Author: Riccardo Mancini
"""

import os
import sys
from io import StringIO

import pytest

@pytest.mark.skip
def path_of(file):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        f"files/{file}"
    )

@pytest.mark.skip
def capture_stdout(fun, args=[], kwargs={}):
    stdout = sys.stdout
    stringio = StringIO()
    sys.stdout = stringio

    fun(*args, **kwargs)

    sys.stdout = stdout
    output = stringio.getvalue()
    stringio.close()

    return output
