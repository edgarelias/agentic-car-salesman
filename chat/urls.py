# chat/urls.py
from rest_framework import routers
from django.urls import path, include
from chat.api_views import ChannelViewSet, MessageViewSet, twilio_inbound

router = routers.DefaultRouter()
router.register(r'channels', ChannelViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    # your DRF router endpoints
    path('', include(router.urls)),
]
