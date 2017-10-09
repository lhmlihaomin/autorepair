"""
Initialize message queue.

Author: lihaomin@tp-link.com.cn
Copyright (C), 2017, TP-LINK Technologies Co., Ltd.
"""
__version__ = "0.0.1"

import pika


def setup_mq(channel, exchanges=[], queues=[], callbacks={}):
    """
    Set up message queue channel.

    Parameters
    ----------
    channel: pika channel
        A pika channel
    exchanges: list of dict
        Must have keys: `name` & `type`
    queues: list of dict
        Must have keys: `name`, `exchange` & `routing_key`
    callbacks: dict
        Queue names as keys, callbacks as values
    
    Returns
    -------
    channel: pika channel
        The channel itself is returned after being set up.

    """
    # Declare exchanges:
    for exchange in exchanges:
        channel.exchange_declare(
            exchange=exchange['name'],
            type=exchange['type']
        )
    # Declare & bind queues:
    for queue in queues:
        channel.queue_declare(
            queue=queue['name'],
            durable=True
        )
        channel.queue_bind(
            queue=queue['name'],
            exchange=queue['exchange'],
            routing_key=queue['routing_key']
        )
    for queue_name in callbacks.keys():
        channel.basic_consume(
            callbacks[queue_name],
            queue=queue_name,
            no_ack=True
        )
    return channel


def init_mq(host, port, username, password, exchanges, queues, callbacks):
    """
    Initialize RabbitMQ connection and channel.

    Parameters
    ---
    host: str
        RabbitMQ service host.
    port: int
        RabbitMQ service port.
    username: str
        RabbitMQ username.
    password: str
        RabbitMQ user password.
    exchanges: list
        Exchange definitions.
    queues: list
        Queue Definitions.
    callbacks: dict
        Queue names as keys, callback functions as values.

    Returns
    ---
    mq_conn: pika connection
    mq_channel: pika channel
    """
    # Init connection:
    mq_conn = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=pika.PlainCredentials(
                username,
                password
            )
        )
    )
    mq_channel = mq_conn.channel()
    mq_channel = setup_mq(
        mq_channel,
        exchanges,
        queues,
        callbacks
    )
    return (mq_conn, mq_channel)



def get_mq_connection(mq_conf, app_name, callbacks = {}):
    """Create and return RabbitMQ connection & queue"""
    app_conf = mq_conf[app_name]
    # Init connection:
    mq_conn = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=mq_conf['host'],
            port=mq_conf['port'],
            credentials=pika.PlainCredentials(
                mq_conf['username'],
                mq_conf['password']
            )
        )
    )
    mq_channel = mq_conn.channel()
    exchanges = app_conf.get('exchanges')
    # exchanges:
    if exchanges is None:
        exchanges = []
    # queues:
    queues = app_conf.get('queues')
    if queues is None:
        queues = []
    # callbacks:
    callback_conf = app_conf.get('callbacks')
    callback_dict = {}
    if callback_conf is not None:
        for qname in callback_conf:
            callback_name = callback_conf[qname]
            callback_dict.update({
                qname: callbacks[callback_name]
            })
    mq_channel = setup_mq(
        mq_channel,
        exchanges,
        queues,
        callback_dict
    )
    return (mq_conn, mq_channel)
