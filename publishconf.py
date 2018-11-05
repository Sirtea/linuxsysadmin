#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

# This file is only used if you use `make publish` or
# explicitly specify it as your config file.

import os
import sys
sys.path.append(os.curdir)
from pelicanconf import *

SITEURL = 'https://www.linuxsysadmin.ml'
RELATIVE_URLS = False

FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/%s.atom.xml'

DELETE_OUTPUT_DIRECTORY = True

# Following items are often useful when publishing

DISQUS_SITENAME = "linuxsysadmin-gmb"
GOOGLE_ANALYTICS = "UA-68486572-1"

# Settings de cookie consent
COOKIE_TEXT = 'De acuerdo a la ley vigente, estoy obligado a informarte de la obviedad de que este sitio utiliza cookies.'

# AdSense settings
ADSENSE_SIDEBAR_NAME = 'Sidebar linuxsysadmin'
ADSENSE_SIDEBAR_CLIENT = 'ca-pub-6984858420847602'
ADSENSE_SIDEBAR_SLOT = '1931313371'

ADSENSE_BANNER_NAME = 'Banner linuxsysadmin'
ADSENSE_BANNER_CLIENT = 'ca-pub-6984858420847602'
ADSENSE_BANNER_SLOT = '7977846974'
