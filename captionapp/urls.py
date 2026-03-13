from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('generator/', views.generator_view, name='generator'),
    path('history/', views.history_view, name='history'),
    path('api/upload/', views.generator_view, name='upload_video'),
    path('api/status/<int:video_id>/', views.check_processing_status, name='check_status'),
    path('api/save/', views.save_caption_view, name='save_caption'),
    path('api/delete/<int:id>/', views.delete_caption_view, name='delete_caption'),
    path('api/delete-video/<int:id>/', views.delete_video_view, name='delete_video'),
]