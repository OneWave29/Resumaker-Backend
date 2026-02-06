# users/tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User


class UserAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # ✅ 네임스페이스 추가: 'users:register'
        self.register_url = reverse("users:register")
        self.login_url = reverse("users:login")
        self.logout_url = reverse("users:logout")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        }

    def test_registration(self):
        """회원가입 성공 테스트"""
        response = self.client.post(self.register_url, self.user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, "testuser")
        self.assertIn("user", response.json())

    def test_registration_with_existing_email(self):
        """중복 이메일 회원가입 실패 테스트"""
        # 첫 번째 유저 생성
        User.objects.create_user(
            username="existinguser", email="test@example.com", password="password123"
        )

        # 같은 이메일로 재등록
        response = self.client.post(
            self.register_url,
            {
                "username": "newuser",
                "email": "test@example.com",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.json())
        self.assertIn("email", response.json()["errors"])


def test_login_logout(self):
    """로그인/로그아웃 테스트"""
    # 유저 생성 - 비밀번호 해시화 확인
    user = User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )

    # 디버깅: 유저가 제대로 생성되었는지 확인
    self.assertTrue(user.check_password("testpass123"))

    # 로그인
    login_response = self.client.post(
        self.login_url,
        {"username": "testuser", "password": "testpass123"},
        format="json",
    )

    # 디버깅: 응답 내용 확인
    if login_response.status_code != status.HTTP_200_OK:
        print(f"Login failed with: {login_response.json()}")

    self.assertEqual(login_response.status_code, status.HTTP_200_OK)
    self.assertIn("user", login_response.json())

    # 로그아웃
    logout_response = self.client.post(self.logout_url)
    self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
