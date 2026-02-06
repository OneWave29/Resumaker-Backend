from django.db import transaction
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema

from .models import Education, Award, Certification, WorkExperience
from .serializers import (
    MyPageResumeSerializer, FileUploadSerializer, 
    ResumeIdSerializer, GeminiResponseSerializer
)
from .services.resume_context import build_db_context
from .services.gemini_resume_writer import generate_resume_with_gemini
from .services.resume_save import save_resume_db_json
from .services.gemini_resume_parser import extract_text_from_pdf, parse_resume_with_gemini

# --- Resume AI ---
@extend_schema(summary="PDF 파싱", request=FileUploadSerializer, responses={200: dict}, tags=["Resume AI"])
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser])
def parse_pdf(request):
    pdf_file = request.FILES.get("file")
    if not pdf_file:
        return Response({"error": "No file"}, status=400)
    pdf_text = extract_text_from_pdf(pdf_file)
    result = parse_resume_with_gemini(pdf_text)
    return Response(result)

@extend_schema(summary="AI 이력서 생성", responses={201: GeminiResponseSerializer}, tags=["Resume AI"])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_resume(request):
    db_payload = build_db_context(request.user)
    try:
        db_json = generate_resume_with_gemini({"frontend": request.data, "db": db_payload})
        resume_obj = save_resume_db_json(request.user, db_json)
        return Response({"resume_id": resume_obj.id, "db_json": db_json}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@extend_schema(summary="PDF 다운로드", request=ResumeIdSerializer, tags=["Resume AI"])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_resume_pdf(request):
    from .services.resume_pdf import render_resume_pdf_from_db
    resume_id = request.data.get("resume_id")
    pdf_bytes = render_resume_pdf_from_db(request.user, int(resume_id))
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
    return response

# --- MyPage ---
@extend_schema(summary="마이페이지 조회/수정", request=MyPageResumeSerializer, responses={200: MyPageResumeSerializer}, tags=["MyPage"])
@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def mypage_resume(request):
    user = request.user
    if request.method == "PUT":
        serializer = MyPageResumeSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                for model, key in [(Education, 'educations'), (Award, 'awards'), 
                                   (Certification, 'certifications'), (WorkExperience, 'work_experiences')]:
                    if key in serializer.validated_data:
                        model.objects.filter(user=user).delete()
                        model.objects.bulk_create([model(user=user, **item) for item in serializer.validated_data[key]])
        else:
            return Response(serializer.errors, status=400)

    data = {
        "educations": Education.objects.filter(user=user).order_by('id'),
        "awards": Award.objects.filter(user=user).order_by('id'),
        "certifications": Certification.objects.filter(user=user).order_by('id'),
        "work_experiences": WorkExperience.objects.filter(user=user).order_by('id'),
    }
    return Response(MyPageResumeSerializer(data).data)

# --- Resume CRUD (Stubs) ---
@extend_schema(summary="목록 조회", tags=["Resume CRUD"])
@api_view(['GET'])
def resume_list(request): return Response([])

@extend_schema(summary="상세 조회", tags=["Resume CRUD"])
@api_view(['GET'])
def resume_read(request, pk): return Response({"id": pk})

@extend_schema(summary="생성", tags=["Resume CRUD"])
@api_view(['POST'])
def resume_create(request): return Response(status=201)

@extend_schema(summary="수정", tags=["Resume CRUD"])
@api_view(['PUT'])
def resume_update(request, pk): return Response(status=200)

@extend_schema(summary="삭제", tags=["Resume CRUD"])
@api_view(['DELETE'])
def resume_delete(request, pk): return Response(status=204)