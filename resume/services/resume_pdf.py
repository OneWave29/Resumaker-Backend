from io import BytesIO
from typing import Dict, Any, List

from django.template.loader import render_to_string

from resume.models import Resume, Element


def _build_resume_view_model(resume: Resume) -> Dict[str, Any]:
    """
    DB(Resume/Element/Content/ContentSubtitle) → 템플릿에서 쓰기 좋은 dict로 변환
    템플릿에서는 resume.items를 돌면서 출력하면 됨.
    """
    order_ids: List[int] = resume.item_list or []

    # item_list가 비어있으면 fallback: 생성 순서대로
    if not order_ids:
        order_ids = list(resume.elements.values_list("id", flat=True))

    elements = (
        Element.objects.filter(resume=resume, id__in=order_ids)
        .select_related("simple_content", "titled_content")
    )
    by_id = {e.id: e for e in elements}

    items: List[Dict[str, Any]] = []
    for eid in order_ids:
        e = by_id.get(eid)
        if not e:
            continue

        if e.type == Element.ElementType.SIMPLE:
            c = getattr(e, "simple_content", None)
            items.append({
                "type": "SIMPLE",
                "sub_title": None,
                "content": (getattr(c, "content", "") if c else ""),
            })
        else:  # TITLED
            t = getattr(e, "titled_content", None)
            items.append({
                "type": "TITLED",
                "sub_title": (getattr(t, "sub_title", "") if t else ""),
                "content": (getattr(t, "content", "") if t else ""),
            })

    # 템플릿에서 resume.items 사용
    return {
        "resume_id": resume.id,
        "items": items,
    }


def render_resume_pdf_from_db(user, resume_id: int) -> bytes:
    """
    user + resume_id로 DB에서 이력서를 읽어 PDF 생성
    (권한 체크 포함: 내 이력서만)
    """
    resume = Resume.objects.filter(id=resume_id, user=user).first()
    if not resume:
        raise ValueError("Resume not found (or no permission).")

    view_model = _build_resume_view_model(resume)

    html_string = render_to_string(
        "resume/resume_pdf.html",
        {"resume": view_model}
    )

    pdf_io = BytesIO()
    HTML(string=html_string).write_pdf(pdf_io)
    return pdf_io.getvalue()


# (선택) 기존 JSON 기반 함수도 유지하고 싶으면 남겨둬도 됨
def render_resume_pdf(resume_json: dict) -> bytes:
    from weasyprint import HTML
    html_string = render_to_string("resume/resume_pdf.html", {"resume": resume_json})
    pdf_io = BytesIO()
    HTML(string=html_string).write_pdf(pdf_io)
    return pdf_io.getvalue()

