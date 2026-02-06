from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserDetailSerializer,
)
from .models import User


@extend_schema(
    tags=['Users'],
    summary='회원가입',
    description='''
    새로운 사용자를 생성합니다.
    
    **필수 필드:**
    - username: 로그인 ID
    - email: 이메일 (고유값)
    - password: 비밀번호 (8자 이상)
    - name: 실명
    - age: 나이
    - gender: 성별 (M/F/O)
    - job: 직업
    - phone_number: 연락처
    ''',
    request=UserRegistrationSerializer,
    responses={
        201: UserDetailSerializer,
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Valid Registration Example',
            value={
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepass123",
                "name": "홍길동",
                "age": 28,
                "gender": "M",
                "job": "백엔드 개발자",
                "phone_number": "010-1234-5678"
            },
            request_only=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """회원가입 API"""
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        user_detail = UserDetailSerializer(user)

        return Response(
            {"message": "User created successfully", "user": user_detail.data},
            status=status.HTTP_201_CREATED,
        )

    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Users'],
    summary='로그인',
    description='''
    이메일과 비밀번호로 로그인합니다.
    
    성공 시 세션 쿠키가 자동으로 설정됩니다.
    ''',
    request=UserLoginSerializer,
    responses={
        200: UserDetailSerializer,
        401: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Login Request',
            value={
                "email": "john@example.com",  # username → email
                "password": "securepass123"
            },
            request_only=True,
        ),
        OpenApiExample(
            'Success Response',
            value={
                "message": "Login successful",
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "name": "홍길동",
                    "age": 28,
                    "gender": "M",
                    "job": "백엔드 개발자",
                    "phone_number": "010-1234-5678",
                    "date_joined": "2026-02-06T12:00:00Z"
                }
            },
            response_only=True,
            status_codes=['200'],
        ),
    ],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """로그인 API (이메일 + 비밀번호)"""
    serializer = UserLoginSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data["email"]  # username → email
        password = serializer.validated_data["password"]

        # 이메일로 유저 찾기
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Django authenticate는 username을 사용하므로 username 전달
        authenticated_user = authenticate(
            request, 
            username=user.username, 
            password=password
        )

        if authenticated_user is not None:
            login(request, authenticated_user)
            user_detail = UserDetailSerializer(authenticated_user)

            return Response(
                {"message": "Login successful", "user": user_detail.data},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Invalid password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Users'],
    summary='로그아웃',
    description='현재 세션을 종료하고 로그아웃합니다.',
    responses={200: OpenApiTypes.OBJECT},
    examples=[
        OpenApiExample(
            'Success Response',
            value={"message": "Logout successful"},
            response_only=True,
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """로그아웃 API"""
    logout(request)
    return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Users'],
    summary='내 정보 조회',
    description='현재 로그인한 사용자의 정보를 조회합니다.',
    responses={200: UserDetailSerializer, 401: OpenApiTypes.OBJECT},
    examples=[
        OpenApiExample(
            'Success Response',
            value={
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "name": "홍길동",
                "age": 28,
                "gender": "M",
                "job": "백엔드 개발자",
                "phone_number": "010-1234-5678",
                "date_joined": "2026-02-06T12:00:00Z"
            },
            response_only=True,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_detail(request):
    """현재 로그인한 유저 정보 조회"""
    serializer = UserDetailSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)