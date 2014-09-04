#!/usr/bin/env python

import sys

from os.path import dirname, realpath, join
from djeasytests.testsetup import TestSetup

__dir__ = realpath(dirname(__file__))

sys.path.insert(0, realpath(join(__dir__, 'testing')))

settings = dict(
    DEBUG=True,
    SITE_ID=1,
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'taggit',
        'taggit_templatetags2',
        'testapp'
    ],
    TEST_RUNNER='django_coverage.coverage_runner.CoverageRunner',
)


testsetup = TestSetup(
    appname='taggit_templatetags2',
    test_settings=settings)

if __name__ == '__main__':
    testsetup.run(__file__)
