from django.urls import path
from . import views

app_name = 'persona'

urlpatterns = [
    path('', views.persona_list, name='persona_list'),
    path('create/', views.persona_create, name='persona_create'),
    path('<int:pk>/', views.persona_read, name='persona_read'),
    path('<int:pk>/update/', views.persona_update, name='persona_update'),
    path('<int:pk>/delete/', views.persona_delete, name='persona_delete'),
]