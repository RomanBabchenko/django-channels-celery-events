from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json


class EventsConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)("events", self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)("events", self.channel_name)

    def events_event(self, event):
        self.send(text_data=json.dumps({
            'message': event["text"],
            'location': event["location"],
            'mode': event["mode"]
        }))
        # self.send(text_data=event["text"])
