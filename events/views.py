from django.shortcuts import render
from .tasks import newuser


def index(request):
    ip = request.META.get('REMOTE_ADDR')
    newuser.delay(ip)
    return render(request, "events/index.html", {})
