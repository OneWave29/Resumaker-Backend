#gemini가 준 json을 형태로 db에 저장하는 부분
import os
import json
import re
from typing import Dict, Any
import google.generativeai as genai


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Gemini가 가끔 JSON 외 텍스트를 섞어 반환할 때를 대비해
    가장 바깥 { ... } 블록을 추출해서 파싱한다.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("Gemini response does not contain a JSON object.")
    return json.loads(m.group(0))


def generate_resume_with_gemini(context: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    # ✅ Gemini가 "DB 저장용 포맷"으로만 반환하도록 강제
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
    {
      "type": "SIMPLE",
      "content": "string"
    },
    {
      "type": "TITLED",
      "sub_title": "string",
      "content": "string"
    }
  ]
}

규칙:
1) frontend를 우선 반영하되, db의 학력/수상/자격/경력은 반드시 item_list에 포함해라.
2) frontend와 db가 충돌하면 사실인 db를 우선하고, frontend는 표현/구성만 반영해라.
3) item_list의 순서는 이력서에서 보여줄 순서다.
4) SIMPLE은 content만 포함한다. (sub_title 금지)
5) TITLED는 sub_title + content를 포함한다.
6) 프로젝트/경력/수상/학력/자격증 등은 적절히 TITLED 또는 SIMPLE로 구성해라.
   - 예: 프로젝트/경력은 TITLED 권장 (sub_title=프로젝트명/회사명-직무 등)
   - 예: 요약/협업스타일/미래목표 등은 SIMPLE 권장
7) content에는 사람이 읽을 수 있도록 줄바꿈과 불릿(-)을 사용해도 된다.
"""

    user = {
        "instruction": "다음 context JSON을 기반으로 이력서를 DB 저장용 JSON으로 생성해줘.",
        "context": context,
        # ✅ 출력 예시를 주면 형식을 더 잘 맞춤
        "output_example": {
            "item_list": [
                {"type": "SIMPLE", "content": "헤드라인\n백엔드 개발자 ..."},
                {"type": "TITLED", "sub_title": "프로젝트: AI 이력서 생성 서비스", "content": "기간: 2024-01 ~ 2024-02\n기술: Django, ...\n- ...\n- ..."}
            ]
        }
    }

    resp = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=[
            {
                "role": "user",
                "parts": [{"text": system + "\n\n" + json.dumps(user, ensure_ascii=False)}],
            }
        ],
        config={
            "temperature": 0.4,
            "response_mime_type": "application/json",
        },
    )

    # ✅ 안전 파싱
    return _extract_json(resp.text)
