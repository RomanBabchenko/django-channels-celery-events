from channels.routing import ProtocolTypeRouter, URLRouter
import events.routing

application = ProtocolTypeRouter(
    {"websocket": URLRouter(events.routing.websocket_urlpatterns)}
)
