from rest_framework import serializers
from .models import Persona

class PersonaSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Persona
        fields = (
            'id',
            'name',
            'description',
            'prompt',
            'user_id',
            'username',
            'is_default',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user_id', 'username', 'is_default', 'created_at', 'updated_at')
    
    def validate_name(self, value):
        """이름 유효성 검사"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name cannot be empty.")
        if len(value) > 50:
            raise serializers.ValidationError("Name must be 50 characters or less.")
        return value
    
    def validate_description(self, value):
        """설명 유효성 검사"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Description cannot be empty.")
        if len(value) > 200:
            raise serializers.ValidationError("Description must be 200 characters or less.")
        return value
    
    def validate_prompt(self, value):
        """프롬프트 유효성 검사"""
        if value and len(value) > 2000:
            raise serializers.ValidationError("Prompt must be 2000 characters or less.")
        return value

class PersonaCreateSerializer(serializers.ModelSerializer):
    """페르소나 생성/수정용 Serializer"""
    
    class Meta:
        model = Persona
        fields = ('name', 'description', 'prompt', 'is_active')
    
    def validate_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name cannot be empty.")
        return value
    
    def validate_description(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Description cannot be empty.")
        return value

class PersonaTemplateSerializer(serializers.Serializer):
    """기본 템플릿 조회용 (DB 저장 X)"""
    name = serializers.CharField()
    description = serializers.CharField()
    prompt = serializers.CharField()