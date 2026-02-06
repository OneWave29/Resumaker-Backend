from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.contrib.auth.decorators import login_required
from .services.resume_context import build_db_context
from .services.gemini_resume_writer import generate_resume_with_gemini
from .services.resume_pdf import render_resume_pdf_from_db
from .services.resume_save import save_resume_db_json

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

@csrf_exempt  # MVP면 유지
@require_POST
@login_required
def generate_resume(request):
    # 1) 프론트 JSON 받기
    try:
        frontend_payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # 2) DB 컨텍스트 만들기
    db_payload = build_db_context(request.user)

    # 3) Gemini에 넘길 context
    context = {
        "frontend": frontend_payload,
        "db": db_payload,
    }

    # 4) Gemini 호출 (DB 저장용 JSON 반환)
    try:
        db_json = generate_resume_with_gemini(context)  # {"item_list":[...]}
    except Exception as e:
        return JsonResponse({"error": "Gemini generation failed", "detail": str(e)}, status=500)

    # 5) 실제 DB 저장
    try:
        resume_obj = save_resume_db_json(request.user, db_json)
    except Exception as e:
        return JsonResponse({"error": "DB save failed", "detail": str(e), "gemini_result": db_json}, status=500)

    # 6) 응답: resume_id + 저장된 결과 JSON
    return JsonResponse(
        {
            "resume_id": resume_obj.id,
            "db_json": db_json,  # 프론트에서 미리보기/수정에 쓰기 좋음
        },
        json_dumps_params={"ensure_ascii": False},
    )

@csrf_exempt
@require_POST
@login_required
def generate_resume_pdf(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    resume_id = payload.get("resume_id")
    if not resume_id:
        return JsonResponse({"error": "resume_id is required"}, status=400)

    try:
        pdf_bytes = render_resume_pdf_from_db(request.user, int(resume_id))
    except Exception as e:
        return JsonResponse({"error": "PDF generation failed", "detail": str(e)}, status=500)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
    return response


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
