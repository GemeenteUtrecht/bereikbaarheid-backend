# -*- coding: utf-8 -*-

import os

from distutils.util import strtobool

from .logging import LOGGING_CONFIG


bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

logconfig_dict = LOGGING_CONFIG

workers = int(os.getenv("GUNICORN_WORKERS", 2))
threads = int(os.getenv("GUNICORN_THREADS", 1))

reload = bool(strtobool(os.getenv("GUNICORN_RELOAD", "false")))

# https://docs.gunicorn.org/en/latest/faq.html#blocking-os-fchmod
# place tmp dir in tmpfs location - instead of overlay - to avoid delays
worker_tmp_dir = "/dev/shm"
