from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Award, Career, Certificate, Education
from .serializers import (
    AwardSerializer,
    CareerSerializer,
    CertificateSerializer,
    EducationSerializer,
    ProfileUpdateSerializer,
)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def replace_profile_info(request):
    serializer = ProfileUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data

    with transaction.atomic():
        Education.objects.filter(user=request.user).delete()
        Award.objects.filter(user=request.user).delete()
        Certificate.objects.filter(user=request.user).delete()
        Career.objects.filter(user=request.user).delete()

        Education.objects.bulk_create(
            [Education(user=request.user, **item) for item in payload["educations"]]
        )
        Award.objects.bulk_create(
            [Award(user=request.user, **item) for item in payload["awards"]]
        )
        Certificate.objects.bulk_create(
            [Certificate(user=request.user, **item) for item in payload["certificates"]]
        )
        Career.objects.bulk_create(
            [Career(user=request.user, **item) for item in payload["careers"]]
        )

    response_data = {
        "educations": EducationSerializer(
            Education.objects.filter(user=request.user), many=True
        ).data,
        "awards": AwardSerializer(Award.objects.filter(user=request.user), many=True).data,
        "certificates": CertificateSerializer(
            Certificate.objects.filter(user=request.user), many=True
        ).data,
        "careers": CareerSerializer(Career.objects.filter(user=request.user), many=True).data,
    }
    return Response(response_data, status=status.HTTP_200_OK)
