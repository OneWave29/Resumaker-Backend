from django.urls import path
from . import views

app_name = 'persona'

urlpatterns = [
    path('', views.persona_list_create, name='persona_list_create'),
    path('<int:pk>/', views.persona_detail, name='persona_detail'),
    path('defaults/', views.default_personas, name='default_personas'),
    
    # AI 면접 관련
    path('interview/', views.ai_interview, name='ai_interview'),
    path('interview/stream/', views.ai_interview_stream, name='ai_interview_stream'),
    path('question/generate/', views.generate_interview_question, name='generate_question'),
]