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
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user_id', 'username', 'created_at', 'updated_at')
    
    def validate_name(self, value):
        """이름 유효성 검사"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name cannot be empty.")
        return value
    
    def validate_description(self, value):
        """설명 유효성 검사"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Description cannot be empty.")
        return value

class PersonaCreateSerializer(serializers.ModelSerializer):
    """페르소나 생성용 Serializer"""
    
    class Meta:
        model = Persona
        fields = ('name', 'description', 'prompt')
    
    def create(self, validated_data):
        # user는 view에서 추가
        return Persona.objects.create(**validated_data)