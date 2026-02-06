from django.urls import path
from . import views

app_name = 'resume'

urlpatterns = [
    path('parse-pdf/', views.parse_pdf, name='parse_pdf'),
    path('generate/', views.generate_resume, name='generate_resume'),
    path('generate-pdf/', views.generate_resume_pdf),
    path('mypage/', views.mypage_resume, name='mypage_resume'),
    path('create/', views.resume_create, name='resume_create'),
    path('<int:pk>/', views.resume_read, name='resume_read'),
    path('<int:pk>/update/', views.resume_update, name='resume_update'),
    path('<int:pk>/delete/', views.resume_delete, name='resume_delete'),
]