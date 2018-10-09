#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Gerard'
SITENAME = u'Linux Sysadmin'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Europe/Madrid'

DEFAULT_LANG = u'es'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
)

# Social widget
SOCIAL = (
    ('GitHub', 'https://github.com/sirtea'),
)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True


# URL format
INDEX_SAVE_AS = 'index.html'
ARCHIVES_URL = 'archives.html'
ARCHIVES_SAVE_AS = 'archives.html'
CATEGORIES_URL = 'categories.html'
CATEGORIES_SAVE_AS = 'categories.html'
CATEGORY_URL = 'category/{slug}.html'
CATEGORY_SAVE_AS = 'category/{slug}.html'
TAGS_URL = 'tags.html'
TAGS_SAVE_AS = 'tags.html'
TAG_URL = 'tag/{slug}.html'
TAG_SAVE_AS = 'tag/{slug}.html'
AUTHORS_URL = 'authors.html'
AUTHORS_SAVE_AS = 'authors.html'
AUTHOR_URL = 'author/{slug}.html'
AUTHOR_SAVE_AS = 'author/{slug}.html'
ARTICLE_URL = '{date:%Y}/{date:%m}/{slug}.html'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{slug}.html'
PAGE_URL = '{slug}.html'
PAGE_SAVE_AS = '{slug}.html'
DRAFT_URL = 'drafts/{slug}.html'
DRAFT_SAVE_AS = 'drafts/{slug}.html'

# Date format
DEFAULT_DATE_FORMAT = '%Y-%m-%d'

# Settings de plugins
PLUGIN_PATHS = ['../../plugins']
PLUGINS = ['sitemap', 'tag_cloud', 'related_posts', 'series', 'readtime']

RELATED_POSTS_TEXT = 'Posts relacionados:'
RELATED_POSTS_MAX = 3

SERIES_TEXT = 'Parte %(index)s de la serie "%(name)s"'

SITEMAP = {
    'format': 'xml',
    'priorities': {
        'articles': 0.5,
        'indexes': 0.5,
        'pages': 0.5
    },
    'changefreqs': {
        'articles': 'monthly',
        'indexes': 'daily',
        'pages': 'monthly'
    }
}

# Settings del theme
THEME = '../../themes/pelican-bootstrap3-gmb'
BOOTSTRAP_THEME = 'cosmo'
PYGMENTS_STYLE = 'vim'
SHOW_ARTICLE_AUTHOR = True
SHOW_ARTICLE_CATEGORY = True
SHOW_DATE_MODIFIED = True
DISPLAY_BREADCRUMBS = True
DISPLAY_CATEGORY_IN_BREADCRUMBS = True
DISPLAY_CATEGORIES_ON_MENU = False
DISPLAY_CATEGORIES_ON_SIDEBAR = True
DISPLAY_TAGS_ON_SIDEBAR = True
DISPLAY_TAGS_INLINE = True
CUSTOM_CSS = 'static/custom.css'

# Static paths
STATIC_PATHS = [
    'images',
    'downloads',
    'extra/custom.css',
    'extra/CNAME',
    'extra/google85de17e42482bf61',
    'extra/css_basic_skeleton',
    'extra/css_basic_styled',
]
EXTRA_PATH_METADATA = {
    'extra/custom.css': {'path': 'static/custom.css'},
    'extra/CNAME': {'path': 'CNAME'},
    'extra/google85de17e42482bf61': {'path': 'google85de17e42482bf61.html'},
    'extra/css_basic_skeleton': {'path': '2018/10/trucos-simples-de-css-para-que-tu-pagina-se-vea-aceptable/css_basic_skeleton.html'},
    'extra/css_basic_styled': {'path': '2018/10/trucos-simples-de-css-para-que-tu-pagina-se-vea-aceptable/css_basic_styled.html'},
}
