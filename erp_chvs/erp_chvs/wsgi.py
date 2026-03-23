"""
WSGI config for erp_chvs project.
"""

import os

try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_chvs.settings')

application = get_wsgi_application()
