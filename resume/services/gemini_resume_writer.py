import os
import json
import re
from typing import Dict, Any

import google.generativeai as genai


def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"Gemini response does not contain a JSON object. Raw: {text[:500]}")
    return json.loads(m.group(0))


def generate_resume_with_gemini(context: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    # ✅ 레거시 방식
    genai.configure(api_key=api_key)

    system = """
너는 이력서 작성 전문가다.
입력 JSON에는 두 영역이 있다.
- frontend: 사용자가 입력한 희망 포맷/초안(우선 반영)
- db: DB에서 조회한 사실 데이터(학력/수상/자격/경력). 과장/추측 금지.

반드시 아래 'DB 저장용 JSON 스키마'로만 출력해라.
설명/코드블록/마크다운/추가 텍스트는 절대 출력하지 마라.

[DB 저장용 JSON 스키마]
{
  "item_list": [
    {"type": "SIMPLE", "content": "string"},
    {"type": "TITLED", "sub_title": "string", "content": "string"}
  ]
}
""".strip()

    user_payload = {
        "instruction": "다음 context JSON을 기반으로 이력서를 DB 저장용 JSON으로 생성해줘.",
        "context": context,
        "output_example": {
            "item_list": [
                {"type": "SIMPLE", "content": "헤드라인\n백엔드 개발자 ..."},
                {
                    "type": "TITLED",
                    "sub_title": "프로젝트: AI 이력서 생성 서비스",
                    "content": "기간: 2024-01 ~ 2024-02\n기술: Django, ...\n- ...\n- ...",
                },
            ]
        },
    }

    prompt = system + "\n\n" + json.dumps(user_payload, ensure_ascii=False)

    # ✅ 모델: 레거시에서 실제로 되는 모델로. (1.5-pro가 404 났으니 flash/pro 최신으로)
    model = genai.GenerativeModel("gemini-2.0-flash")
    resp = model.generate_content(prompt)

    text = getattr(resp, "text", "") or ""
    return _extract_json(text)
