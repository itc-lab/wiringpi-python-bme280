#!/usr/bin/ python3
# -*- coding:utf-8 -*-

import sys

sys.path.insert(0, "/var/www/flask")
from app_relay import app_relay

application = app_relay
