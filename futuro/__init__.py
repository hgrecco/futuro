# -*- coding: utf-8 -*-
"""
    futuro
    ~~~~~~

    A `concurrent.futures` playground.

    :copyright: 2013 by Hernan E. Grecco, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from .tasks import TasksGroup
from .implicitfutures import ThreadPoolExecutor
