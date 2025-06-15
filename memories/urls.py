from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_admin import PendingMemoriesView

router = DefaultRouter()
# Register viewsets without the 'memories' prefix since it's already in the main URLs
router.register(r'', views.MemoryViewSet, basename='memory')

# Custom actions
urlpatterns = [
    path('', include(router.urls)),
    # Add custom actions
    path('<int:pk>/like/', views.MemoryViewSet.as_view({'post': 'like'}), name='memory-like'),
    path('top-liked/', views.MemoryViewSet.as_view({'get': 'top_liked'}), name='top-liked'),
    path('my-memories/', views.MemoryViewSet.as_view({'get': 'my_memories'}), name='my-memories'),
    
    # Admin endpoints
    path('admin/pending-memories/', PendingMemoriesView.as_view(), name='pending-memories'),
    path('admin/pending-memories/<int:memory_id>/', PendingMemoriesView.as_view(), name='manage-memory'),
]
