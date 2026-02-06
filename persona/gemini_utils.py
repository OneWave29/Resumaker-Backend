import google.generativeai as genai
from django.conf import settings

def configure_gemini():
    """Gemini API 설정"""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    
    genai.configure(api_key=settings.GEMINI_API_KEY)

def get_gemini_response(persona_prompt, user_message, conversation_history=None):
    """
    Gemini로부터 응답 받기
    
    Args:
        persona_prompt (str): 페르소나의 시스템 프롬프트
        user_message (str): 사용자 메시지
        conversation_history (list): 이전 대화 내역 (선택)
    
    Returns:
        str: AI 응답
    """
    configure_gemini()
    
    # Gemini 모델 선택
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=persona_prompt
    )
    
    # 대화 시작
    chat = model.start_chat(history=conversation_history or [])
    
    # 응답 생성
    response = chat.send_message(user_message)
    
    return response.text

def get_gemini_streaming_response(persona_prompt, user_message, conversation_history=None):
    """
    Gemini 스트리밍 응답 받기
    
    Args:
        persona_prompt (str): 페르소나의 시스템 프롬프트
        user_message (str): 사용자 메시지
        conversation_history (list): 이전 대화 내역
    
    Yields:
        str: AI 응답 청크
    """
    configure_gemini()
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=persona_prompt
    )
    
    chat = model.start_chat(history=conversation_history or [])
    
    response = chat.send_message(user_message, stream=True)
    
    for chunk in response:
        yield chunk.text