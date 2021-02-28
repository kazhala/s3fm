from unittest import TestCase
import doctest
from s3fm import app


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(app))
    return tests


class TestApp(TestCase):
    def test_app(self):
        self.assertEqual(1, 1)
