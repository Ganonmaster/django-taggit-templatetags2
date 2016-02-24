#!/usr/bin/env python
import os
from os.path import abspath, join, realpath, dirname
import sys

import django
from django.conf import settings


__dir__ = realpath(dirname(__file__))
sys.path.insert(0, realpath(__dir__))
sys.path.insert(0, realpath(join(__dir__, 'testing')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.settings")


def runtests():
    if hasattr(django, 'setup'):
        django.setup()
    try:
        from django.test.runner import DiscoverRunner
        runner_class = DiscoverRunner
        test_args = ['test_project.testapp']
    except ImportError:
        from django.test.simple import DjangoTestSuiteRunner
        runner_class = DjangoTestSuiteRunner
        test_args = ['test_project.testapp']
    failures = runner_class(failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == "__main__":
    runtests(*sys.argv[1:])
