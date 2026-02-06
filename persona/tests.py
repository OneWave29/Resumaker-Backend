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
        
        self.persona_list_url = reverse('persona:persona_list_create')
        self.default_personas_url = reverse('persona:default_personas')
    
    def test_create_persona(self):
        """페르소나 생성 테스트"""
        data = {
            'name': '테스트 면접관',
            'description': '테스트용 면접관입니다',
            'prompt': '테스트 프롬프트'
        }
        
        response = self.client.post(self.persona_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Persona.objects.count(), 1)
        self.assertEqual(Persona.objects.get().name, '테스트 면접관')
    
    def test_create_persona_without_prompt(self):
        """프롬프트 없이 페르소나 생성 테스트 (NULL 허용)"""
        data = {
            'name': '프롬프트 없는 면접관',
            'description': '프롬프트가 없습니다'
        }
        
        response = self.client.post(self.persona_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(Persona.objects.get().prompt)
    
    def test_list_personas(self):
        """페르소나 목록 조회 테스트"""
        Persona.objects.create(
            name='면접관1',
            description='설명1',
            user=self.user
        )
        Persona.objects.create(
            name='면접관2',
            description='설명2',
            user=self.user
        )
        
        response = self.client.get(self.persona_list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
    
    def test_get_default_personas(self):
        """기본 페르소나 조회 테스트"""
        response = self.client.get(self.default_personas_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)
        
        personas = response.json()
        persona_names = [p['name'] for p in personas]
        
        self.assertIn('데이터 분석가', persona_names)
        self.assertIn('정통 대기업 임원', persona_names)
        self.assertIn('스타트업 CEO', persona_names)
        self.assertIn('효율 중시형', persona_names)
    
    def test_update_persona(self):
        """페르소나 수정 테스트"""
        persona = Persona.objects.create(
            name='원본 이름',
            description='원본 설명',
            user=self.user
        )
        
        url = reverse('persona:persona_detail', args=[persona.id])
        data = {'name': '수정된 이름'}
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        persona.refresh_from_db()
        self.assertEqual(persona.name, '수정된 이름')
    
    def test_delete_persona(self):
        """페르소나 삭제 테스트"""
        persona = Persona.objects.create(
            name='삭제할 면접관',
            description='삭제 테스트',
            user=self.user
        )
        
        url = reverse('persona:persona_detail', args=[persona.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Persona.objects.count(), 0)