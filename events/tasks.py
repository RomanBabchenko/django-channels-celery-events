import logging
from time import sleep

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
import requests


channel_layer = get_channel_layer()
logger = logging.getLogger()


@shared_task
def newuser(ip):
    sleep(1)
    logger.info(ip)
    print(ip)
    async_to_sync(channel_layer.group_send)("events", {"type": "events.event", "text": "NEW USER CONNECTED", "location": ip, "mode": "info"})
