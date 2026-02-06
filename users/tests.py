from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User

class UserAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')
        
        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': '김테스트',
            'age': 25,
            'gender': 'M',
            'job': '개발자',
            'phone_number': '010-1234-5678'
        }
    
    def test_registration_success(self):
        """회원가입 성공 테스트"""
        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
        user = User.objects.get()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.name, '김테스트')
        self.assertEqual(user.age, 25)
        self.assertEqual(user.gender, 'M')
        self.assertEqual(user.job, '개발자')
        self.assertEqual(user.phone_number, '010-1234-5678')
    
    def test_registration_missing_fields(self):
        """필수 필드 누락 시 실패 테스트"""
        invalid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
            # name, age, gender, job, phone_number 누락
        }
        
        response = self.client.post(
            self.register_url,
            invalid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.json())
    
    def test_registration_duplicate_email(self):
        """중복 이메일 회원가입 실패 테스트"""
        User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='password123',
            name='기존유저',
            age=30,
            gender='F',
            job='디자이너',
            phone_number='010-9999-9999'
        )
        
        response = self.client.post(
            self.register_url,
            self.valid_user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.json()['errors'])
    
    def test_login_logout(self):
        """로그인/로그아웃 테스트"""
        # 유저 생성
        User.objects.create_user(
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
        login_response = self.client.post(
            self.login_url,
            {
                'username': 'testuser',
                'password': 'testpass123'
            },
            format='json'
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('user', login_response.json())
        self.assertEqual(login_response.json()['user']['name'], '김테스트')
        
        # 로그아웃
        logout_response = self.client.post(self.logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)