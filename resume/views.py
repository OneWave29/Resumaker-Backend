from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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
