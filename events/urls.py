from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_admin import PendingEventsView, PendingPhotosView

router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')

# Nested router for event photos
from rest_framework_nested import routers
event_router = routers.NestedSimpleRouter(router, r'events', lookup='event')
event_router.register(r'photos', views.EventPhotoViewSet, basename='event-photo')

app_name = 'events'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(event_router.urls)),
    
    # Admin endpoints
    path('admin/', include([
        path('pending-events/', PendingEventsView.as_view(), name='pending-events'),
        path('pending-events/<int:event_id>/', PendingEventsView.as_view(), name='manage-event'),
        path('pending-photos/', PendingPhotosView.as_view(), name='pending-photos'),
        path('pending-photos/<int:photo_id>/', PendingPhotosView.as_view(), name='manage-photo'),
    ])),
]
