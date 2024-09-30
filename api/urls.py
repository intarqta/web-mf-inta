from django.urls import path, include
from rest_framework import routers
from api import views
from .views import NDVIAPIView

rourter = routers.DefaultRouter()
rourter.register('api', views.TaskView, 'api')


urlpatterns = [
    path("api/v1/", include(rourter.urls)),
    path('ndvi/', NDVIAPIView.as_view(), name='ndvi'),
]