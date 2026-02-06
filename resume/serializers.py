from rest_framework import serializers

from .models import Award, Career, Certificate, Education


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            "id",
            "school_name",
            "major",
            "admission_year",
            "graduation_year",
            "gpa",
        ]
        read_only_fields = ["id"]


class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = [
            "id",
            "contest_name",
            "award_detail",
            "award_year",
            "organizer",
        ]
        read_only_fields = ["id"]


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = [
            "id",
            "name",
            "obtained_date",
            "issuer",
            "score",
            "grade",
        ]
        read_only_fields = ["id"]


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Career
        fields = [
            "id",
            "company_name",
            "join_date",
            "leave_date",
            "position",
            "position_detail",
        ]
        read_only_fields = ["id"]


class ProfileUpdateSerializer(serializers.Serializer):
    educations = EducationSerializer(many=True, required=True)
    awards = AwardSerializer(many=True, required=True)
    certificates = CertificateSerializer(many=True, required=True)
    careers = CareerSerializer(many=True, required=True)
