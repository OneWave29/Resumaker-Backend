from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from persona.models import Persona

User = get_user_model()

@receiver(post_save, sender=User)
def create_default_personas(sender, instance, created, **kwargs):
    """새 유저 생성 시 기본 페르소나 4개 자동 생성"""
    if created:
        default_personas = [
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
        
        for persona_data in default_personas:
            Persona.objects.create(
                user=instance,
                name=persona_data['name'],
                description=persona_data['description'],
                prompt=persona_data['prompt'],
                is_default=True,
                is_active=True
            )