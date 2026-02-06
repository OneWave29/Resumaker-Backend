from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        min_length=8,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = (
            'id',
            'username',      # 로그인 ID
            'email',         # 이메일
            'password',      # 비밀번호
            'name',          # 실명
            'age',           # 나이
            'gender',        # 성별
            'job',           # 직업
            'phone_number',  # 연락처
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'name': {'required': True},
            'age': {'required': True},
            'gender': {'required': True},
            'job': {'required': True},
            'phone_number': {'required': True},
        }
    
    def validate_email(self, value):
        """이메일 중복 체크"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
    def validate_username(self, value):
        """유저명 중복 체크"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
    def validate_age(self, value):
        """나이 유효성 검사"""
        if value < 0 or value > 150:
            raise serializers.ValidationError("Please enter a valid age.")
        return value
    
    def validate_phone_number(self, value):
        """전화번호 중복 체크 (선택사항)"""
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value
    
    def create(self, validated_data):
        """유저 생성"""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            age=validated_data['age'],
            gender=validated_data['gender'],
            job=validated_data['job'],
            phone_number=validated_data['phone_number']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class UserDetailSerializer(serializers.ModelSerializer):
    """유저 상세 정보 (비밀번호 제외)"""
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'name',
            'age',
            'gender',
            'job',
            'phone_number',
            'date_joined',
        )
        read_only_fields = ('id', 'username', 'date_joined')