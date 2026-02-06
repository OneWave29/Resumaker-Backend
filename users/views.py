from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer,
    UserDetailSerializer
)
from .models import User

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    회원가입 API
    
    요청 필드:
    - username: 로그인 ID (필수)
    - email: 이메일 (필수, 고유)
    - password: 비밀번호 (필수, 8자 이상)
    - name: 실명 (필수)
    - age: 나이 (필수)
    - gender: 성별 (필수, M/F/O)
    - job: 직업 (필수)
    - phone_number: 연락처 (필수)
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        user_detail = UserDetailSerializer(user)
        
        return Response({
            'message': 'User created successfully',
            'user': user_detail.data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """로그인 API"""
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            user_detail = UserDetailSerializer(user)
            
            return Response({
                'message': 'Login successful',
                'user': user_detail.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """로그아웃 API"""
    logout(request)
    return Response({
        'message': 'Logout successful'
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request):
    """현재 로그인한 유저 정보 조회"""
    serializer = UserDetailSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)