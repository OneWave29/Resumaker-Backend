from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema

from .models import Education, Award, Certification, WorkExperience, Resume, Element, Content, ContentSubtitle
from .serializers import (
    MyPageResumeSerializer, FileUploadSerializer, 
    ResumeIdSerializer, GeminiResponseSerializer
)
from .services.resume_context import build_db_context
from .services.gemini_resume_writer import generate_resume_with_gemini
from .services.resume_save import save_resume_db_json
from .services.gemini_resume_parser import extract_text_from_pdf, parse_resume_with_gemini

# --- Helper Functions (Internal) ---

def _serialize_resume_summary(resume: Resume) -> dict:
    return {
        "resume_id": resume.id,
        "created_at": resume.created_at.isoformat(),
        "updated_at": resume.updated_at.isoformat(),
        "item_count": len(resume.item_list or []),
    }

def _serialize_resume_detail(resume: Resume) -> dict:
    order_ids = resume.item_list or []
    if not order_ids:
        order_ids = list(resume.elements.values_list("id", flat=True).order_by("id"))

    elements = (
        Element.objects.filter(resume=resume, id__in=order_ids)
        .select_related("simple_content", "titled_content")
    )
    by_id = {e.id: e for e in elements}

    items = []
    for eid in order_ids:
        e = by_id.get(eid)
        if not e: continue
        if e.type == Element.ElementType.SIMPLE:
            c = getattr(e, "simple_content", None)
            items.append({
                "element_id": e.id, "type": "SIMPLE", "sub_title": None,
                "content": (getattr(c, "content", "") if c else ""),
            })
        else:
            t = getattr(e, "titled_content", None)
            items.append({
                "element_id": e.id, "type": "TITLED",
                "sub_title": (getattr(t, "sub_title", "") if t else ""),
                "content": (getattr(t, "content", "") if t else ""),
            })
    return {
        "resume_id": resume.id, "created_at": resume.created_at.isoformat(),
        "updated_at": resume.updated_at.isoformat(), "item_list": order_ids, "items": items,
    }

# --- 1. Resume AI (AI 기능) ---

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
@permission_classes([AllowAny])
def generate_resume(request):
    # 비로그인 유저 대응
    if request.user.is_anonymous:
        db_payload = {"awards": [], "educations": [], "certifications": [], "work_experiences": []}
    else:
        db_payload = build_db_context(request.user)

    try:
        db_json = generate_resume_with_gemini({"frontend": request.data, "db": db_payload})
        # 비로그인이면 저장 스킵
        if request.user.is_anonymous:
            return Response({"resume_id": None, "db_json": db_json}, status=200)
            
        resume_obj = save_resume_db_json(request.user, db_json)
        return Response({"resume_id": resume_obj.id, "db_json": db_json}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@extend_schema(summary="PDF 결과물 생성", request=ResumeIdSerializer, tags=["Resume AI"])
@api_view(['POST'])
@permission_classes([AllowAny])
def generate_resume_pdf(request):
    from .services.resume_pdf import render_resume_pdf_from_db
    resume_id = request.data.get("resume_id")
    if not resume_id:
        return Response({"error": "resume_id is required"}, status=400)
    
    try:
        pdf_bytes = render_resume_pdf_from_db(request.user, int(resume_id))
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
        return response
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# --- 2. MyPage (기본 정보 관리) ---

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
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    data = {
        "educations": Education.objects.filter(user=user).order_by('id'),
        "awards": Award.objects.filter(user=user).order_by('id'),
        "certifications": Certification.objects.filter(user=user).order_by('id'),
        "work_experiences": WorkExperience.objects.filter(user=user).order_by('id'),
    }
    return Response(MyPageResumeSerializer(data).data)

# --- 3. Resume CRUD (개별 이력서 관리) ---

@extend_schema(summary="이력서 목록 조회", tags=["Resume CRUD"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resume_list(request):
    qs = Resume.objects.filter(user=request.user).order_by("-updated_at")
    data = [_serialize_resume_summary(r) for r in qs]
    return Response({"results": data})

@extend_schema(summary="이력서 상세 조회", tags=["Resume CRUD"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resume_read(request, pk):
    resume = get_object_or_404(Resume, id=pk, user=request.user)
    return Response(_serialize_resume_detail(resume))

@extend_schema(summary="이력서 수정", tags=["Resume CRUD"])
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def resume_update(request, pk):
    resume = get_object_or_404(Resume, id=pk, user=request.user)
    items = request.data.get("item_list")
    if not isinstance(items, list):
        return Response({"error": "item_list must be a list"}, status=400)

    resume.elements.all().delete()
    new_order = []
    for item in items:
        t = item.get("type")
        el = Element.objects.create(resume=resume, type=t)
        new_order.append(el.id)
        if t == Element.ElementType.SIMPLE:
            Content.objects.create(element=el, content=item.get("content", "") or "")
        else:
            ContentSubtitle.objects.create(
                element=el, sub_title=item.get("sub_title", "") or "", content=item.get("content", "") or ""
            )

    resume.item_list = new_order
    resume.updated_at = timezone.now()
    resume.save(update_fields=["item_list", "updated_at"])
    return Response(_serialize_resume_detail(resume))

@extend_schema(summary="이력서 삭제", tags=["Resume CRUD"])
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def resume_delete(request, pk):
    resume = get_object_or_404(Resume, id=pk, user=request.user)
    resume.delete()
    return Response(status=204)

@extend_schema(summary="이력서 생성(빈 양식)", tags=["Resume CRUD"])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resume_create(request):
    resume = Resume.objects.create(user=request.user)
    return Response(_serialize_resume_summary(resume), status=201)