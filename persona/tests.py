from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from .models import Persona

class PersonaTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # 테스트 유저 생성
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='김테스트',
            age=25,
            gender='M',
            job='개발자',
            phone_number='010-1234-5678'
        )
        
        # 로그인
        self.client.force_authenticate(user=self.user)
        
        # URL 설정
        self.persona_list_url = reverse('persona:persona_list_create')
        self.templates_url = reverse('persona:persona_templates')
        self.create_from_template_url = reverse('persona:create_from_template')
    
    def test_get_persona_templates(self):
        """페르소나 템플릿 조회 테스트"""
        response = self.client.get(self.templates_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('templates', response.json())
        self.assertEqual(len(response.json()['templates']), 4)
        
        templates = response.json()['templates']
        template_names = [t['name'] for t in templates]
        
        self.assertIn('데이터 분석가', template_names)
        self.assertIn('정통 대기업 임원', template_names)
        self.assertIn('스타트업 CEO', template_names)
        self.assertIn('효율 중시형', template_names)
    
    def test_create_persona_from_template(self):
        """템플릿 기반 페르소나 생성 테스트"""
        data = {
            'template_name': '데이터 분석가'
        }
        
        response = self.client.post(
            self.create_from_template_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Persona.objects.count(), 1)
        
        persona = Persona.objects.first()
        self.assertEqual(persona.name, '데이터 분석가')
        self.assertEqual(persona.user, self.user)
        self.assertFalse(persona.is_default)
    
    def test_create_custom_persona_from_template(self):
        """템플릿 기반 커스텀 페르소나 생성 테스트"""
        data = {
            'template_name': '데이터 분석가',
            'custom_name': '친절한 데이터 분석가',
            'custom_description': '친절하게 질문하는 면접관',
            'custom_prompt': '친절한 톤으로 질문하세요.'
        }
        
        response = self.client.post(
            self.create_from_template_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        persona = Persona.objects.first()
        self.assertEqual(persona.name, '친절한 데이터 분석가')
        self.assertEqual(persona.description, '친절하게 질문하는 면접관')
    
    def test_create_completely_custom_persona(self):
        """완전히 새로운 커스텀 페르소나 생성 테스트"""
        data = {
            'name': '나만의 면접관',
            'description': '내가 만든 면접관',
            'prompt': '나만의 프롬프트'
        }
        
        response = self.client.post(
            self.persona_list_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Persona.objects.count(), 1)
        
        persona = Persona.objects.first()
        self.assertEqual(persona.name, '나만의 면접관')
        self.assertFalse(persona.is_default)
    
    def test_create_persona_without_prompt(self):
        """프롬프트 없이 페르소나 생성 테스트 (NULL 허용)"""
        data = {
            'name': '프롬프트 없는 면접관',
            'description': '프롬프트가 없습니다'
        }
        
        response = self.client.post(
            self.persona_list_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(Persona.objects.get().prompt)
    
    def test_list_personas(self):
        """페르소나 목록 조회 테스트"""
        Persona.objects.create(
            name='면접관1',
            description='설명1',
            user=self.user,
            is_default=False
        )
        Persona.objects.create(
            name='면접관2',
            description='설명2',
            user=self.user,
            is_default=False
        )
        
        response = self.client.get(self.persona_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['personas']), 2)
    
    def test_list_custom_personas_only(self):
        """커스텀 페르소나만 조회 테스트"""
        Persona.objects.create(
            name='기본 페르소나',
            description='기본',
            user=self.user,
            is_default=True
        )
        Persona.objects.create(
            name='커스텀 페르소나',
            description='커스텀',
            user=self.user,
            is_default=False
        )
        
        url = f"{self.persona_list_url}?custom_only=true"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        personas = response.json()['personas']
        self.assertEqual(len(personas), 1)
        self.assertEqual(personas[0]['name'], '커스텀 페르소나')
    
    def test_update_custom_persona(self):
        """커스텀 페르소나 수정 테스트"""
        persona = Persona.objects.create(
            name='원본 이름',
            description='원본 설명',
            user=self.user,
            is_default=False
        )
        
        url = reverse('persona:persona_detail', args=[persona.id])
        data = {'name': '수정된 이름'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        persona.refresh_from_db()
        self.assertEqual(persona.name, '수정된 이름')
    
    def test_cannot_update_default_persona(self):
        """기본 페르소나 수정 불가 테스트"""
        persona = Persona.objects.create(
            name='기본 페르소나',
            description='기본',
            user=self.user,
            is_default=True
        )
        
        url = reverse('persona:persona_detail', args=[persona.id])
        data = {'name': '수정 시도'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_duplicate_persona(self):
        """페르소나 복제 테스트"""
        original = Persona.objects.create(
            name='원본',
            description='원본 설명',
            prompt='원본 프롬프트',
            user=self.user,
            is_default=True
        )
        
        url = reverse('persona:duplicate_persona', args=[original.id])
        data = {
            'custom_name': '복사본',
            'custom_prompt': '수정된 프롬프트'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Persona.objects.count(), 2)
        
        duplicate = Persona.objects.exclude(id=original.id).first()
        self.assertEqual(duplicate.name, '복사본')
        self.assertEqual(duplicate.prompt, '수정된 프롬프트')
        self.assertFalse(duplicate.is_default)
    
    def test_toggle_persona_active(self):
        """페르소나 활성화/비활성화 테스트"""
        persona = Persona.objects.create(
            name='테스트',
            description='설명',
            user=self.user,
            is_active=True
        )
        
        url = reverse('persona:toggle_active', args=[persona.id])
        
        # 비활성화
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        persona.refresh_from_db()
        self.assertFalse(persona.is_active)
        
        # 다시 활성화
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        persona.refresh_from_db()
        self.assertTrue(persona.is_active)
    
    def test_delete_custom_persona(self):
        """커스텀 페르소나 삭제 테스트"""
        persona = Persona.objects.create(
            name='삭제할 면접관',
            description='삭제 테스트',
            user=self.user,
            is_default=False
        )
        
        url = reverse('persona:persona_detail', args=[persona.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Persona.objects.count(), 0)
    
    def test_cannot_delete_default_persona(self):
        """기본 페르소나 삭제 불가 테스트"""
        persona = Persona.objects.create(
            name='기본 페르소나',
            description='기본',
            user=self.user,
            is_default=True
        )
        
        url = reverse('persona:persona_detail', args=[persona.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Persona.objects.count(), 1)
    
    def test_ai_interview_with_inactive_persona(self):
        """비활성화된 페르소나로 면접 시도 테스트"""
        persona = Persona.objects.create(
            name='비활성 면접관',
            description='설명',
            user=self.user,
            is_active=False
        )
        
        url = reverse('persona:ai_interview')
        data = {
            'persona_id': persona.id,
            'message': '테스트 메시지'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('deactivated', response.json()['error'])