from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

app_name = 'gcprojects'

urlpatterns = [
    path('', include(router.urls)),
] 