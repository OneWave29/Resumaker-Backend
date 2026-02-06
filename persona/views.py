# persona/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from django.utils import timezone
from .models import Persona
from .serializers import PersonaSerializer, PersonaCreateSerializer
from .gemini_utils import get_gemini_response, get_gemini_streaming_response
import json

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def persona_list_create(request):
    """
    GET: 현재 유저의 모든 페르소나 조회
    POST: 새 페르소나 생성
    """
    if request.method == 'GET':
        personas = Persona.objects.filter(user=request.user)
        serializer = PersonaSerializer(personas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = PersonaCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            persona = serializer.save(user=request.user)
            response_serializer = PersonaSerializer(persona)
            return Response({
                'message': 'Persona created successfully',
                'persona': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def persona_detail(request, pk):
    """
    GET: 특정 페르소나 조회
    PUT: 페르소나 수정
    DELETE: 페르소나 삭제
    """
    try:
        persona = Persona.objects.get(pk=pk, user=request.user)
    except Persona.DoesNotExist:
        return Response({
            'error': 'Persona not found or you do not have permission'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = PersonaSerializer(persona)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = PersonaCreateSerializer(persona, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            response_serializer = PersonaSerializer(persona)
            return Response({
                'message': 'Persona updated successfully',
                'persona': response_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        persona.delete()
        return Response({
            'message': 'Persona deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([AllowAny])
def default_personas(request):
    """기본 제공 페르소나 4종 조회"""
    default_personas_data = [
        {
            'name': '데이터 분석가',
            'description': '정확한 수치와 데이터 근거를 중시하며 논리적인 비약이 없는지 체크',
            'prompt': '당신은 데이터 분석가 면접관입니다. 지원자의 답변에서 구체적인 수치, 데이터 근거, 논리적 일관성을 중점적으로 평가하세요. 모호한 표현이나 근거 없는 주장에 대해서는 반드시 추가 질문을 통해 명확히 하세요.',
        },
        {
            'name': '정통 대기업 임원',
            'description': '지원자의 말투, 태도, 기술 스택, 학력 등 기본기를 가장 중요하게 평가',
            'prompt': '당신은 전통적인 대기업의 임원 면접관입니다. 지원자의 예의바른 태도, 정확한 언어 사용, 체계적인 학력 및 경력, 검증된 기술 스택을 중시하세요. 기본에 충실한 인재를 선호하며, 안정적이고 신뢰할 수 있는 답변을 높이 평가합니다.',
        },
        {
            'name': '스타트업 CEO',
            'description': '기존의 틀을 깨는 혁신적인 사고와 빠른 실행력을 가진 인재를 선호',
            'prompt': '당신은 혁신적인 스타트업의 CEO 면접관입니다. 기존 관습에 도전하는 창의적 사고, 빠른 의사결정과 실행력, 실패에서 배우는 자세를 중시하세요. 학력이나 경력보다는 문제 해결 능력과 성장 가능성에 주목하세요.',
        },
        {
            'name': '효율 중시형',
            'description': '불필요한 수식어 없이 핵심만 담은 짧고 명확한 답변을 선호',
            'prompt': '당신은 효율성을 최우선으로 하는 면접관입니다. 지원자가 핵심을 간결하게 전달하는지 평가하세요. 장황한 설명이나 불필요한 수식어는 감점 요소입니다. STAR 기법처럼 구조화되고 명확한 답변을 선호합니다.',
        }
    ]
    
    return Response(default_personas_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_interview(request):
    """
    Gemini를 사용한 AI 면접관과 대화
    
    요청 필드:
    - persona_id: 사용할 페르소나 ID (필수)
    - message: 사용자 메시지 (필수)
    - conversation_history: 이전 대화 내역 (선택)
      [
        {"role": "user", "parts": ["메시지"]},
        {"role": "model", "parts": ["응답"]}
      ]
    """
    persona_id = request.data.get('persona_id')
    user_message = request.data.get('message')
    conversation_history = request.data.get('conversation_history', [])
    
    # 필수 필드 검증
    if not persona_id or not user_message:
        return Response({
            'error': 'persona_id and message are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 페르소나 조회
    try:
        persona = Persona.objects.get(pk=persona_id, user=request.user)
    except Persona.DoesNotExist:
        return Response({
            'error': 'Persona not found or you do not have permission'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # 시스템 프롬프트 설정
        system_prompt = persona.prompt or f"""
당신은 '{persona.name}' 페르소나의 면접관입니다.
설명: {persona.description}

면접관으로서 지원자의 답변을 평가하고, 적절한 후속 질문을 하세요.
"""
        
        # Gemini로부터 응답 받기
        ai_response = get_gemini_response(
            persona_prompt=system_prompt,
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        return Response({
            'persona': {
                'id': persona.id,
                'name': persona.name,
                'description': persona.description
            },
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({
            'error': f'API configuration error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            'error': f'Failed to get AI response: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_interview_stream(request):
    """
    Gemini를 사용한 AI 면접 (스트리밍 응답)
    
    Server-Sent Events (SSE) 방식으로 실시간 응답 전달
    """
    persona_id = request.data.get('persona_id')
    user_message = request.data.get('message')
    conversation_history = request.data.get('conversation_history', [])
    
    if not persona_id or not user_message:
        return Response({
            'error': 'persona_id and message are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        persona = Persona.objects.get(pk=persona_id, user=request.user)
    except Persona.DoesNotExist:
        return Response({
            'error': 'Persona not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    def stream_response():
        """스트리밍 응답 생성"""
        try:
            system_prompt = persona.prompt or f"""
당신은 '{persona.name}' 페르소나의 면접관입니다.
설명: {persona.description}
"""
            
            for chunk in get_gemini_streaming_response(
                persona_prompt=system_prompt,
                user_message=user_message,
                conversation_history=conversation_history
            ):
                yield f"data: {json.dumps({'chunk': chunk, 'done': False}, ensure_ascii=False)}\n\n"
            
            # 완료 신호
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True}, ensure_ascii=False)}\n\n"
    
    response = StreamingHttpResponse(
        stream_response(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    
    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_interview_question(request):
    """
    페르소나 기반 면접 질문 생성
    
    요청 필드:
    - persona_id: 사용할 페르소나 ID (필수)
    - job_position: 지원 직무 (선택)
    - resume_summary: 이력서 요약 (선택)
    """
    persona_id = request.data.get('persona_id')
    job_position = request.data.get('job_position', '지원 직무')
    resume_summary = request.data.get('resume_summary', '')
    
    if not persona_id:
        return Response({
            'error': 'persona_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        persona = Persona.objects.get(pk=persona_id, user=request.user)
    except Persona.DoesNotExist:
        return Response({
            'error': 'Persona not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # 질문 생성용 프롬프트
        system_prompt = f"""
당신은 '{persona.name}' 페르소나의 면접관입니다.
설명: {persona.description}

지원자 정보:
- 지원 직무: {job_position}
{f"- 이력서 요약: {resume_summary}" if resume_summary else ""}

이 지원자에게 적절한 면접 질문을 1개만 생성하세요.
질문만 답변하고 다른 설명은 하지 마세요.
"""
        
        question = get_gemini_response(
            persona_prompt=system_prompt,
            user_message="면접 질문을 생성해주세요."
        )
        
        return Response({
            'persona': {
                'id': persona.id,
                'name': persona.name,
            },
            'question': question.strip(),
            'job_position': job_position,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to generate question: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)