from typing import Dict, Any, List
from django.db import transaction

from resume.models import Resume, Element, Content, ContentSubtitle


@transaction.atomic
def save_resume_db_json(user, db_json: Dict[str, Any]) -> Resume:
    """
    Gemini가 반환한 DB 저장용 JSON을 실제 DB에 저장.
    db_json 예시:
    {
      "item_list": [
        {"type":"SIMPLE","content":"..."},
        {"type":"TITLED","sub_title":"...","content":"..."}
      ]
    }
    """
    items = db_json.get("item_list")
    if not isinstance(items, list):
        raise ValueError("db_json.item_list must be a list")

    # 1) Resume 생성
    resume = Resume.objects.create(user=user, item_list=[])

    element_ids_in_order: List[int] = []

    # 2) item_list 순회: Element + Content/ContentSubtitle 생성
    for item in items:
        if not isinstance(item, dict):
            continue

        t = item.get("type")
        if t not in (Element.ElementType.SIMPLE, Element.ElementType.TITLED):
            raise ValueError(f"Invalid element type: {t}")

        el = Element.objects.create(resume=resume, type=t)
        element_ids_in_order.append(el.id)

        if t == Element.ElementType.SIMPLE:
            Content.objects.create(
                element=el,
                content=item.get("content", "") or "",
            )
        else:  # TITLED
            ContentSubtitle.objects.create(
                element=el,
                sub_title=item.get("sub_title", "") or "",
                content=item.get("content", "") or "",
            )

    # 3) Resume.item_list 업데이트
    resume.item_list = element_ids_in_order
    resume.save(update_fields=["item_list", "updated_at"])

    return resume
