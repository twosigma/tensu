#!/usr/bin/env python3

import doctest
import unittest
from app import display
from app import utils
from app.utils import Utils
from tests.test_display import DisplayTests
from tests.test_utils import UtilTests
from tests.test_sensu_go import SensuGoHelperTests


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(display))
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


unittest.main()
