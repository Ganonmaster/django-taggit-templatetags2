#!/usr/bin/env python
from djeasytests.testsetup import TestSetup

settings = dict(
    DEBUG=True,
    SITE_ID=1,
    INSTALLED_APPS = [
        'django.contrib.contenttypes',
        'taggit',
        'taggit_classy',
        'taggit_classy_testapp'       
    ]
)

testsetup = TestSetup(appname='taggit_classy', test_settings=settings)

if __name__ == '__main__':
    testsetup.run(__file__)