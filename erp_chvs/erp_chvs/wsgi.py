"""
WSGI config for erp_chvs project.
"""

import os

# Solo parchear en producción (gunicorn). El runserver de Django no lo necesita
# y monkey.patch_all() rompe el servidor de desarrollo con Python 3.13.
import sys
_dev_server = any('runserver' in arg for arg in sys.argv)
if not _dev_server:
    try:
        from gevent import monkey
        monkey.patch_all()
    except ImportError:
        pass

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')

application = get_wsgi_application()
