import json
import os
from pypdf import PdfReader
from google import genai

# 프론트 폼에 맞춰서 "반환 JSON 스키마"를 고정해두는 게 핵심
SCHEMA_EXAMPLE = {
    "resume_format": None,
    "target_role": None,
    "headline": None,
    "strength_keywords": [],
    "projects": [
        {
            "start": None,         # "YYYY-MM" 권장
            "end": None,           # "YYYY-MM" 또는 "present"
            "title": None,
            "bullets": [],
            "tech_stack": []
        }
    ],
    "collaboration_style": None,
    "main_tech_stack": [],
    "future_goal": None
}

def extract_text_from_pdf(file_obj) -> str:
    """UploadedFile(메모리/임시파일)에서 텍스트 추출"""
    reader = PdfReader(file_obj)
    texts = []
    for page in reader.pages:
        t = page.extract_text() or ""
        texts.append(t)
    return "\n".join(texts).strip()

def _clean_json(text: str) -> str:
    """Gemini가 ```json ...``` 같은 걸 붙일 때 대비"""
    text = text.strip()
    if "```" in text:
        # 코드블록 제거
        text = text.replace("```json", "").replace("```", "").strip()
    # 첫 { ~ 마지막 }만 잘라내기(방어)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

def parse_resume_with_gemini(pdf_text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    prompt = f"""
너는 '이력서 PDF 텍스트'를 모바일 폼에 자동 채우기 위한 JSON 파서다.

규칙:
- 반드시 JSON만 출력한다. 설명, 마크다운, 코드블록 금지.
- 아래 스키마의 key를 절대 변경하지 말 것.
- 정보가 없으면 null 또는 빈 배열([])로 둔다.
- 날짜는 "YYYY-MM" 형식으로 통일한다.

스키마 예시:
{json.dumps(SCHEMA_EXAMPLE, ensure_ascii=False)}

이력서 텍스트:
\"\"\"{pdf_text[:12000]}\"\"\"
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text or ""
    cleaned = _clean_json(raw)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "error": "Gemini JSON parsing failed",
            "raw": raw[:2000]
        }
