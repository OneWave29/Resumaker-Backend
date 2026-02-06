from django.db import models
from users.models import User

class Persona(models.Model):
    """면접관 페르소나 모델"""
    
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    prompt = models.TextField(null=True, blank=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='personas',
        db_column='user_id'
    )
    is_default = models.BooleanField(default=False)  # 기본 제공 페르소나 여부
    is_active = models.BooleanField(default=True)  # 활성화 여부
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'persona'
        ordering = ['-is_default', 'id']  # 기본 페르소나 우선
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
    
    def __str__(self):
        return f"{self.name} - {self.user.username} {'(Default)' if self.is_default else ''}"