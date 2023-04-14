#!/usr/bin/env python3

import doctest
import unittest
from app import display
from app import utils
from tests.test_display import DisplayTests  # noqa
from tests.test_utils import UtilTests  # noqa
from tests.test_sensu_go import SensuGoHelperTests  # noqa
from tests.test_tensu import TensuTests  # noqa


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(display))
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


unittest.main()
