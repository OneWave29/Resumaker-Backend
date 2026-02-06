from django.db import models
from users.models import User

class Persona(models.Model):
    """면접관 페르소나 모델"""
    
    name = models.CharField(max_length=255)  # NOT NULL
    description = models.CharField(max_length=255)  # NOT NULL
    prompt = models.TextField(null=True, blank=True)  # Nullable
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='personas',
        db_column='user_id'
    )  # NOT NULL
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'persona'
        ordering = ['id']
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"