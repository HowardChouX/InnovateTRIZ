# -*- coding: utf-8 -*-
"""
TRIZ应用工具模块
"""

from .logger import (
    TRIZLogger,
    get_logger,
    get_triz_logger,
    log_call,
    log_async_call,
    log_info,
    log_debug,
    log_warning,
    log_error,
    IS_ANDROID,
    is_android,
    LOG_FILE,
    TEST_LOG_FILE,
    LOG_DIR
)

__all__ = [
    "TRIZLogger",
    "get_logger",
    "get_triz_logger",
    "log_call",
    "log_async_call",
    "log_info",
    "log_debug",
    "log_warning",
    "log_error",
    "IS_ANDROID",
    "is_android",
    "LOG_FILE",
    "TEST_LOG_FILE",
    "LOG_DIR"
]
