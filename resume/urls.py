from django.urls import path
from . import views

app_name = 'resume'

urlpatterns = [
    path('parse-pdf/', views.parse_pdf, name='parse_pdf'),
    path('generate/', views.generate_resume, name='generate_resume'),
    path('generate-pdf/', views.generate_resume_pdf),
]