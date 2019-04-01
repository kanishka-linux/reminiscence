from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__title__ = 'Reminiscence: Self-hosted bookmark and archive manager'
__version__ = '0.3.0'
__author__ = 'kanishka-linux (AAK)'
__license__ = 'AGPLv3'
__copyright__ = 'Copyright (C) 2018 kanishka-linux (AAK) kanishka.linux@gmail.com'
