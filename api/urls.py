from django.urls import path, include
from rest_framework import routers
from api import views
from .views import NDVIAPIView
from rest_framework.documentation import include_docs_urls
# from .views import PastureAvailabilityAPIView

urlpatterns = [
    path('ndvi/', NDVIAPIView.as_view(), name='ndvi'),
    # path('disponibilidad/', PastureAvailabilityAPIView.as_view(), name='pasto-disponibilidad'),
]
