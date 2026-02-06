# persona/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.db.models import Q
from .models import Persona
from .serializers import (
    PersonaSerializer, 
    PersonaCreateSerializer,
    PersonaTemplateSerializer,
    InterviewRequestSerializer,
    InterviewResponseSerializer,
    QuestionGenerateRequestSerializer,
    QuestionGenerateResponseSerializer
)
from .gemini_utils import get_gemini_response, get_gemini_streaming_response
import json

# 기본 제공 페르소나 템플릿
DEFAULT_PERSONA_TEMPLATES = [
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

@extend_schema(
    tags=['Personas'],
    summary='페르소나 템플릿 조회',
    description='기본 제공 페르소나 템플릿 목록을 조회합니다.',
    responses={
        200: PersonaTemplateSerializer(many=True)
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def persona_templates(request):
    """기본 제공 페르소나 템플릿 조회"""
    serializer = PersonaTemplateSerializer(DEFAULT_PERSONA_TEMPLATES, many=True)
    return Response({
        'templates': serializer.data,
        'count': len(DEFAULT_PERSONA_TEMPLATES)
    }, status=status.HTTP_200_OK)

@extend_schema(
    tags=['Personas'],
    summary='템플릿 기반 페르소나 생성',
    description='기본 템플릿을 기반으로 페르소나를 생성합니다.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'template_name': {'type': 'string', 'example': '데이터 분석가'},
                'custom_name': {'type': 'string', 'example': '나만의 데이터 분석가'},
                'custom_description': {'type': 'string', 'example': '커스텀 설명'},
                'custom_prompt': {'type': 'string', 'example': '커스텀 프롬프트'}
            },
            'required': ['template_name']
        }
    },
    responses={
        201: PersonaSerializer,
        400: OpenApiExample('Error', value={'error': 'template_name is required'}),
        404: OpenApiExample('Not Found', value={'error': 'Template not found'})
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_persona_from_template(request):
    """템플릿 기반 페르소나 생성"""
    template_name = request.data.get('template_name')
    
    if not template_name:
        return Response({
            'error': 'template_name is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    template = next(
        (t for t in DEFAULT_PERSONA_TEMPLATES if t['name'] == template_name),
        None
    )
    
    if not template:
        return Response({
            'error': f'Template "{template_name}" not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    persona_data = {
        'name': request.data.get('custom_name', template['name']),
        'description': request.data.get('custom_description', template['description']),
        'prompt': request.data.get('custom_prompt', template['prompt']),
        'is_active': True
    }
    
    serializer = PersonaCreateSerializer(data=persona_data)
    
    if serializer.is_valid():
        persona = serializer.save(
            user=request.user,
            is_default=False
        )
        response_serializer = PersonaSerializer(persona)
        return Response({
            'message': 'Persona created from template successfully',
            'persona': response_serializer.data,
            'based_on_template': template_name
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['Personas'],
    summary='페르소나 목록 조회 / 생성',
    description='GET: 사용자의 페르소나 목록 조회, POST: 새 페르소나 생성',
    parameters=[
        OpenApiParameter('default_only', OpenApiTypes.BOOL, description='기본 페르소나만 조회'),
        OpenApiParameter('custom_only', OpenApiTypes.BOOL, description='커스텀 페르소나만 조회'),
        OpenApiParameter('active_only', OpenApiTypes.BOOL, description='활성화된 페르소나만 조회'),
    ],
    request=PersonaCreateSerializer,
    responses={
        200: PersonaSerializer(many=True),
        201: PersonaSerializer,
        400: OpenApiExample('Error', value={'errors': {}})
    }
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def persona_list_create(request):
    """페르소나 목록 조회 및 생성"""
    if request.method == 'GET':
        queryset = Persona.objects.filter(user=request.user)
        
        if request.query_params.get('default_only') == 'true':
            queryset = queryset.filter(is_default=True)
        
        if request.query_params.get('custom_only') == 'true':
            queryset = queryset.filter(is_default=False)
        
        if request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        
        serializer = PersonaSerializer(queryset, many=True)
        return Response({
            'personas': serializer.data,
            'count': len(serializer.data)
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = PersonaCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            persona = serializer.save(
                user=request.user,
                is_default=False
            )
            response_serializer = PersonaSerializer(persona)
            return Response({
                'message': 'Custom persona created successfully',
                'persona': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['Personas'],
    summary='페르소나 상세 조회 / 수정 / 삭제',
    description='GET: 조회, PUT/PATCH: 수정, DELETE: 삭제 (커스텀 페르소나만 가능)',
    request=PersonaCreateSerializer,
    responses={
        200: PersonaSerializer,
        204: OpenApiExample('Deleted', value={'message': 'Persona deleted successfully'}),
        403: OpenApiExample('Forbidden', value={'error': 'Cannot modify default persona'}),
        404: OpenApiExample('Not Found', value={'error': 'Persona not found'})
    }
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def persona_detail(request, pk):
    """페르소나 상세 조회/수정/삭제"""
    try:
        persona = Persona.objects.get(pk=pk, user=request.user)
    except Persona.DoesNotExist:
        return Response({
            'error': 'Persona not found or you do not have permission'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = PersonaSerializer(persona)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        if persona.is_default:
            return Response({
                'error': 'Cannot modify default persona. Create a custom copy instead.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        partial = request.method == 'PATCH'
        serializer = PersonaCreateSerializer(persona, data=request.data, partial=partial)
        
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
        if persona.is_default:
            return Response({
                'error': 'Cannot delete default persona'
            }, status=status.HTTP_403_FORBIDDEN)
        
        persona.delete()
        return Response({
            'message': 'Persona deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

@extend_schema(
    tags=['Personas'],
    summary='페르소나 복제',
    description='기존 페르소나를 복제하여 새 커스텀 페르소나를 생성합니다.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'custom_name': {'type': 'string', 'example': '복사된 페르소나'},
                'custom_description': {'type': 'string'},
                'custom_prompt': {'type': 'string'}
            }
        }
    },
    responses={
        201: PersonaSerializer,
        404: OpenApiExample('Not Found', value={'error': 'Persona not found'})
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def duplicate_persona(request, pk):
    """페르소나 복제"""
    try:
        original = Persona.objects.get(pk=pk, user=request.user)
    except Persona.DoesNotExist:
        return Response({
            'error': 'Persona not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    duplicate = Persona.objects.create(
        user=request.user,
        name=request.data.get('custom_name', f"{original.name} (복사본)"),
        description=request.data.get('custom_description', original.description),
        prompt=request.data.get('custom_prompt', original.prompt),
        is_default=False,
        is_active=True
    )
    
    serializer = PersonaSerializer(duplicate)
    return Response({
        'message': 'Persona duplicated successfully',
        'original_id': original.id,
        'persona': serializer.data
    }, status=status.HTTP_201_CREATED)

@extend_schema(
    tags=['Personas'],
    summary='페르소나 활성화/비활성화 토글',
    description='페르소나의 활성화 상태를 토글합니다.',
    responses={
        200: PersonaSerializer,
        404: OpenApiExample('Not Found', value={'error': 'Persona not found'})
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_persona_active(request, pk):
    """페르소나 활성화/비활성화 토글"""
    try:
        persona = Persona.objects.get(pk=pk, user=request.user)
    except Persona.DoesNotExist:
        return Response({
            'error': 'Persona not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    persona.is_active = not persona.is_active
    persona.save()
    
    serializer = PersonaSerializer(persona)
    return Response({
        'message': f'Persona {"activated" if persona.is_active else "deactivated"}',
        'persona': serializer.data
    }, status=status.HTTP_200_OK)

@extend_schema(
    tags=['Personas'],
    summary='AI 면접관과 대화',
    description='선택한 페르소나로 AI 면접관과 대화합니다.',
    request=InterviewRequestSerializer,
    responses={
        200: InterviewResponseSerializer,
        400: OpenApiExample('Error', value={'error': 'persona_id and message are required'}),
        404: OpenApiExample('Not Found', value={'error': 'Persona not found'})
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_interview(request):
    """AI 면접관과 대화"""
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
            'error': 'Persona not found or you do not have permission'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not persona.is_active:
        return Response({
            'error': 'This persona is deactivated'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        system_prompt = persona.prompt or f"""
당신은 '{persona.name}' 페르소나의 면접관입니다.
설명: {persona.description}

면접관으로서 지원자의 답변을 평가하고, 적절한 후속 질문을 하세요.
"""
        
        ai_response = get_gemini_response(
            persona_prompt=system_prompt,
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        return Response({
            'persona': {
                'id': persona.id,
                'name': persona.name,
                'description': persona.description,
                'is_default': persona.is_default
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

@extend_schema(
    tags=['Personas'],
    summary='페르소나 기반 면접 질문 생성',
    description='선택한 페르소나를 기반으로 맞춤형 면접 질문을 생성합니다.',
    request=QuestionGenerateRequestSerializer,
    responses={
        200: QuestionGenerateResponseSerializer,
        400: OpenApiExample('Error', value={'error': 'persona_id is required'}),
        404: OpenApiExample('Not Found', value={'error': 'Persona not found'})
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_interview_question(request):
    """페르소나 기반 면접 질문 생성"""
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
    
    if not persona.is_active:
        return Response({
            'error': 'This persona is deactivated'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
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