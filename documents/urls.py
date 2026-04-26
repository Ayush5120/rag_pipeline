# Place at: docqa/documents/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet)
# This one line creates all these URLs:
# GET    /api/documents/
# POST   /api/documents/
# GET    /api/documents/{id}/
# PUT    /api/documents/{id}/
# DELETE /api/documents/{id}/
# GET    /api/documents/{id}/chunks/      ← your @action
# POST   /api/documents/{id}/reprocess/  ← your @action

urlpatterns = [path('', include(router.urls))]