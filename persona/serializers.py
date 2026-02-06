from rest_framework import serializers
from resume.models import Education, Award, Certification, WorkExperience
from .models import Persona

# --- 기초 데이터 시리얼라이저 ---
class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'university', 'major', 'enrollment_year', 'graduation_year', 'gpa']

class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = ['id', 'competition_name', 'award_title', 'award_year', 'awarding_organization']

class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['id', 'name', 'obtained_date', 'issuing_organization', 'score', 'grade']

class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = ['id', 'company_name', 'start_year', 'end_year', 'job_title', 'job_description']

# --- 통합 요청/응답 시리얼라이저 ---
class MyPageResumeSerializer(serializers.Serializer):
    educations = EducationSerializer(many=True, required=False)
    awards = AwardSerializer(many=True, required=False)
    certifications = CertificationSerializer(many=True, required=False)
    work_experiences = WorkExperienceSerializer(many=True, required=False)

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="PDF 파일을 업로드하세요.")

class ResumeIdSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField(help_text="생성된 이력서의 ID")

class GeminiResponseSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField()
    db_json = serializers.JSONField()

# --- Persona 시리얼라이저 ---
class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = '__all__'

class PersonaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = '__all__'

class PersonaTemplateSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    prompt = serializers.CharField()

class InterviewRequestSerializer(serializers.Serializer):
    persona_id = serializers.IntegerField()
    message = serializers.CharField()
    conversation_history = serializers.ListField(required=False, default=list)

class InterviewResponseSerializer(serializers.Serializer):
    persona = PersonaSerializer()
    user_message = serializers.CharField()
    ai_response = serializers.CharField()
    timestamp = serializers.DateTimeField()

class QuestionGenerateRequestSerializer(serializers.Serializer):
    persona_id = serializers.IntegerField()
    job_position = serializers.CharField(required=False)
    resume_summary = serializers.CharField(required=False)

class QuestionGenerateResponseSerializer(serializers.Serializer):
    persona = PersonaSerializer()
    question = serializers.CharField()
    job_position = serializers.CharField()
    timestamp = serializers.DateTimeField()