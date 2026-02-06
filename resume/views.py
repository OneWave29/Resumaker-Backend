from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils.dateparse import parse_date
from decimal import Decimal, InvalidOperation
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Education, Award, Certification, WorkExperience
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.contrib.auth.decorators import login_required
from .services.resume_context import build_db_context
from .services.gemini_resume_writer import generate_resume_with_gemini
from .services.resume_save import save_resume_db_json
from rest_framework.permissions import AllowAny

from .services.gemini_resume_parser import (
    extract_text_from_pdf,
    parse_resume_with_gemini,
)

# =========================
# API: PDF 업로드 → JSON 반환
# POST /resume/parse-pdf/
# =========================
@csrf_exempt  # 해커톤 MVP면 일단 유지(프론트 붙일 때 CSRF 막힘 방지)
@require_POST
def parse_pdf(request):
    if "file" not in request.FILES:
        return JsonResponse({"error": "file is required"}, status=400)

    pdf_file = request.FILES["file"]

    # 1) PDF → 텍스트 추출
    pdf_text = extract_text_from_pdf(pdf_file)
    if not pdf_text:
        return JsonResponse(
            {"error": "텍스트를 추출할 수 없습니다. 스캔본 PDF일 수 있습니다."},
            status=400,
        )

    # 2) Gemini 호출 → JSON 생성
    try:
        result = parse_resume_with_gemini(pdf_text)
        return JsonResponse(result, json_dumps_params={"ensure_ascii": False})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =========================
# (선택) 임시 테스트 페이지
# GET /resume/
# 프론트 붙이면 지워도 됨
# =========================
def upload_test_page(request):
    html = """
    <html>
      <body>
        <h2>PDF 업로드 테스트</h2>
        <form action="/resume/parse-pdf/" method="post" enctype="multipart/form-data">
          <input type="file" name="file" accept="application/pdf" />
          <button type="submit">업로드</button>
        </form>
        <p>결과는 JSON으로 바로 뜹니다.</p>
      </body>
    </html>
    """
    return HttpResponse(html)

# ...

@api_view(["POST"])
@permission_classes([AllowAny])  # 테스트용
def generate_resume(request):
    frontend_payload = request.data or {}

    # ✅ (1) 익명이면 DB 컨텍스트는 빈 값으로
    if request.user.is_anonymous:
        db_payload = {
            "awards": [],
            "educations": [],
            "certifications": [],
            "work_experiences": [],
        }
    else:
        db_payload = build_db_context(request.user)

    context = {"frontend": frontend_payload, "db": db_payload}

    try:
        db_json = generate_resume_with_gemini(context)
    except Exception as e:
        return Response(
            {"error": "Gemini generation failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # ✅ (2) 익명이면 DB 저장 스킵하고 생성 결과만 반환
    if request.user.is_anonymous:
        return Response(
            {"db_json": db_json, "resume_id": None},
            status=status.HTTP_200_OK,
        )

    try:
        resume_obj = save_resume_db_json(request.user, db_json)
    except Exception as e:
        return Response(
            {"error": "DB save failed", "detail": str(e), "gemini_result": db_json},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"resume_id": resume_obj.id, "db_json": db_json},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
#@permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def generate_resume_pdf(request):
    from .services.resume_pdf import render_resume_pdf_from_db

    payload = request.data or {}
    resume_id = payload.get("resume_id")
    if not resume_id:
        return Response({"error": "resume_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pdf_bytes = render_resume_pdf_from_db(request.user, int(resume_id))
    except Exception as e:
        return Response(
            {"error": "PDF generation failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="resume.pdf"'
    return resp

# =========================
# TODO: Resume CRUD (나중에 구현)
# =========================
def resume_list(request):
    return JsonResponse({"message": "TODO resume_list"}, status=501)

def resume_create(request):
    return JsonResponse({"message": "TODO resume_create"}, status=501)

def resume_read(request, resume_id):
    return JsonResponse({"message": f"TODO resume_read {resume_id}"}, status=501)

def resume_update(request, resume_id):
    return JsonResponse({"message": f"TODO resume_update {resume_id}"}, status=501)

def resume_delete(request, resume_id):
    return JsonResponse({"message": f"TODO resume_delete {resume_id}"}, status=501)


def _serialize_education(item):
    return {
        "id": item.id,
        "university": item.university,
        "major": item.major,
        "enrollment_year": item.enrollment_year,
        "graduation_year": item.graduation_year,
        "gpa": item.gpa,
    }


def _serialize_award(item):
    return {
        "id": item.id,
        "competition_name": item.competition_name,
        "award_title": item.award_title,
        "award_year": item.award_year,
        "awarding_organization": item.awarding_organization,
    }


def _serialize_certification(item):
    return {
        "id": item.id,
        "name": item.name,
        "obtained_date": item.obtained_date.isoformat(),
        "issuing_organization": item.issuing_organization,
        "score": item.score,
        "grade": item.grade,
    }


def _serialize_work_experience(item):
    return {
        "id": item.id,
        "company_name": item.company_name,
        "start_year": item.start_year,
        "end_year": item.end_year,
        "job_title": item.job_title,
        "job_description": item.job_description,
    }


def _coerce_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer")


def _coerce_int_optional(value, field_name):
    if value in (None, ""):
        return None
    return _coerce_int(value, field_name)


def _coerce_decimal_optional(value, field_name):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} must be a decimal number")


def _coerce_text_optional(value):
    if value in (None, ""):
        return None
    return value


def _validate_required_fields(item, fields, section_name):
    missing = [
        field for field in fields if field not in item or item[field] in (None, "")
    ]
    if missing:
        raise ValueError(f"{section_name} missing fields: {', '.join(missing)}")


def _replace_items(
    model,
    user,
    items,
    required_fields,
    optional_fields,
    section_name,
    normalizers=None,
):
    if normalizers is None:
        normalizers = {}
    if not isinstance(items, list):
        raise ValueError(f"{section_name} must be a list")

    model.objects.filter(user=user).delete()
    new_items = []
    for raw in items:
        if not isinstance(raw, dict):
            raise ValueError(f"{section_name} items must be objects")
        _validate_required_fields(raw, required_fields, section_name)
        payload = {}
        for field in required_fields:
            value = raw[field]
            if field in normalizers:
                value = normalizers[field](value)
            payload[field] = value
        for field in optional_fields:
            if field in raw:
                value = raw.get(field)
                if field in normalizers:
                    value = normalizers[field](value)
                payload[field] = value
        new_items.append(model(user=user, **payload))
    model.objects.bulk_create(new_items)


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def mypage_resume(request):
    """
    마이페이지 학력/수상/자격증/경력 일괄 조회 및 수정 (GET/PUT)

    - GET: 현재 데이터를 조회합니다. 없으면 빈 배열을 반환합니다.
    - PUT: body에 목록이 포함되면 해당 목록을 전체 교체합니다.
      body가 비어 있으면 현재 데이터를 그대로 조회합니다.
    """
    user = request.user
    payload = request.data or {}

    sections = {
        "educations": (
            Education,
            ["university", "major", "enrollment_year", "graduation_year"],
            ["gpa"],
            {
                "enrollment_year": lambda v: _coerce_int(v, "enrollment_year"),
                "graduation_year": lambda v: _coerce_int(v, "graduation_year"),
                "gpa": lambda v: _coerce_decimal_optional(v, "gpa"),
            },
        ),
        "awards": (
            Award,
            ["competition_name", "award_title", "award_year", "awarding_organization"],
            [],
            {
                "award_year": lambda v: _coerce_int(v, "award_year"),
            },
        ),
        "certifications": (
            Certification,
            ["name", "obtained_date", "issuing_organization"],
            ["score", "grade"],
            {
                "obtained_date": lambda v: (
                    parse_date(v)
                    if parse_date(v)
                    else (_ for _ in ()).throw(ValueError("obtained_date must be YYYY-MM-DD"))
                ),
                "score": lambda v: _coerce_int_optional(v, "score"),
                "grade": _coerce_text_optional,
            },
        ),
        "work_experiences": (
            WorkExperience,
            ["company_name", "start_year", "job_title", "job_description"],
            ["end_year"],
            {
                "start_year": lambda v: _coerce_int(v, "start_year"),
                "end_year": lambda v: _coerce_int_optional(v, "end_year"),
            },
        ),
    }

    if request.method == "PUT":
        try:
            with transaction.atomic():
                for section_name, (model, required_fields, optional_fields, normalizers) in sections.items():
                    if section_name in payload:
                        _replace_items(
                            model=model,
                            user=user,
                            items=payload.get(section_name, []),
                            required_fields=required_fields,
                            optional_fields=optional_fields,
                            section_name=section_name,
                            normalizers=normalizers,
                        )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "educations": [
                _serialize_education(item)
                for item in Education.objects.filter(user=user).order_by("id")
            ],
            "awards": [
                _serialize_award(item)
                for item in Award.objects.filter(user=user).order_by("id")
            ],
            "certifications": [
                _serialize_certification(item)
                for item in Certification.objects.filter(user=user).order_by("id")
            ],
            "work_experiences": [
                _serialize_work_experience(item)
                for item in WorkExperience.objects.filter(user=user).order_by("id")
            ],
        },
        status=status.HTTP_200_OK,
    )
