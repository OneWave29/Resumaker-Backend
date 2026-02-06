from django.urls import path
from . import views

app_name = 'persona'

urlpatterns = [
    # 템플릿 관련
    path('templates/', views.persona_templates, name='persona_templates'),
    path('templates/create/', views.create_persona_from_template, name='create_from_template'),
    
    # CRUD
    path('', views.persona_list_create, name='persona_list_create'),
    path('<int:pk>/', views.persona_detail, name='persona_detail'),
    path('<int:pk>/duplicate/', views.duplicate_persona, name='duplicate_persona'),
    path('<int:pk>/toggle/', views.toggle_persona_active, name='toggle_active'),
    
    # AI 면접
    path('interview/', views.ai_interview, name='ai_interview'),
    path('question/generate/', views.generate_interview_question, name='generate_question'),
]