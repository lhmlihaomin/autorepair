import json

def queue_notification(channel, event):
    """Push a notification to MQ for sending."""
    exchange_name = "topic_notifications"
    routing_key_prefix = "notifications.notification"
    channel.basic_publish(
        exchange=exchange_name,
        routing_key=".".join([routing_key_prefix, event['event_type']]),
        body=json.dumps(event)
    )



def queue_exception(channel, exception):
    """Push an exception info to MQ for sending."""
    exchange_name = "topic_exceptions"
    routing_key_prefix = "notifications.exception"
    pass


def send_mail(ses_client, from_address, to_addresses, subject, body):
    """Send an email with SES API."""
    response = ses_client.send_email(
        Source=from_address,
        Destination={
            'ToAddresses': to_addresses
        },
        Message={
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8',
            },
            'Body': {
                'Text': {
                    'Data': body,
                    'Charset': 'UTF-8',
                }
            }
        },
    )
    return response


def send_notification_mail(ses_client, from_address, to_addresses, event):
    """Prepare the args for notification emails."""
    subject = "[AUTOREPAIR] New Event"
    body = ""
    for key in event.keys():
        body += "%s: \t%s\r\n"%(key, str(event[key]))
    return send_mail(ses_client, from_address, to_addresses, subject, body)


def send_exception_mail(ses_client, from_address, to_addresses, exception):
    subject = "[AUTOREPAIR] Exception"
    body = str(exception)
    return send_mail(ses_client, from_address, to_addresses, subject, body)
