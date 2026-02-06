from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # username은 AbstractUser에서 상속 (자동 NOT NULL)
    email = models.EmailField(unique=True)  # NOT NULL (기본값)
    name = models.CharField(max_length=255)  # 실명
    age = models.BigIntegerField()  # NOT NULL
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)  # NOT NULL
    job = models.CharField(max_length=255)  # NOT NULL
    phone_number = models.CharField(max_length=255)  # NOT NULL

    def __str__(self):
        return f"{self.name} ({self.username})"
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'