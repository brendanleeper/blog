import os

WTF_CSRF_ENABLED = True
with open('secretkey', 'r') as secret:
    SECRET_KEY = secret.read().replace('\n', '')
DEBUG = True

APP_ROOT = os.path.dirname(os.path.realpath(__file__))
DATABASE = 'sqliteext:///%s' % os.path.join(APP_ROOT, 'blog.db')

SITE_WIDTH = 800
