from rest_framework import serializers
from persona.models import Persona
from .models import Education, Award, Certification, WorkExperience

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

class MyPageResumeSerializer(serializers.Serializer):
    educations = EducationSerializer(many=True, required=False)
    awards = AwardSerializer(many=True, required=False)
    certifications = CertificationSerializer(many=True, required=False)
    work_experiences = WorkExperienceSerializer(many=True, required=False)

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="PDF 파일을 업로드하세요.")

class ResumeIdSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField(help_text="생성된 이력서의 고유 ID")

class GeminiResponseSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField()
    db_json = serializers.JSONField(help_text="Gemini가 생성한 데이터")