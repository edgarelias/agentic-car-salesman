from rest_framework import routers
from django.urls import path, include
from catalog.views_api import VehicleViewSet, KnowledgeArticleViewSet

router = routers.DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'knowledge_articles', KnowledgeArticleViewSet, basename='knowledgearticle')

urlpatterns = [
    path('', include(router.urls)),
]
