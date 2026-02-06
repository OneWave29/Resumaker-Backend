from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = "MALE", "MALE"
        FEMALE = "FEMALE", "FEMALE"

    email = models.EmailField(unique=True, null=False, blank=False)
    name = models.CharField(max_length=255, default="")
    age = models.BigIntegerField(default=0)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)
    job = models.CharField(max_length=255, default="")
    phone_number = models.CharField(max_length=255, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email