"""
Consume messages from related message queues, and send them out through SES
service.

Usage: python notification.py

Author: lihaomin@tp-link.com.cn
Copyright (C), 2017, TP-LINK Technologies Co., Ltd.
"""
__version__ = "0.1.0"

from .core import send_mail, send_notification_mail, send_exception_mail, \
    queue_notification, queue_exception
