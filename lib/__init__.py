#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# 文件: __init__.py
# 说明:

'''tools'''

__all__ = [
    # 日志记录
    'debug', 'info', 'warn', 'error', 'critical', 'logexception'
]

from .logger import logger

debug = logger.debug
info = logger.info
warn = logger.warning
error = logger.error
critical = logger.critical
logexception = logger.exception
