"""
URL configuration for agent_chatbot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core.views_api import credentials_check
from chat.api_views import twilio_inbound

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/authentication/', include('rest_framework.urls', namespace='rest_framework')),
    
    path('api/chat/', include('chat.urls')),
    path('api/catalog/', include('catalog.urls')),
    path('api/credentials_check/', credentials_check, name='credentials-check'),
    path('api/twilio/inbound/', twilio_inbound, name='twilio-inbound'),


]
