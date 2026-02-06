from django.conf import settings
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Education(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    school_name = models.CharField(max_length=255)
    major = models.CharField(max_length=255)
    admission_year = models.PositiveSmallIntegerField(default=0)
    graduation_year = models.PositiveSmallIntegerField(default=0)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.school_name} - {self.major}"


class Award(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contest_name = models.CharField(max_length=255, default="")
    award_detail = models.TextField(default="")
    award_year = models.PositiveSmallIntegerField(default=0)
    organizer = models.CharField(max_length=255, default="")

    def __str__(self):
        return self.contest_name


class Certificate(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    obtained_date = models.DateField(default=timezone.now)
    issuer = models.CharField(max_length=255, default="")
    score = models.CharField(max_length=255, null=True, blank=True)
    grade = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Career(TimestampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    join_date = models.DateField(default=timezone.now)
    leave_date = models.DateField(null=True, blank=True)
    position = models.CharField(max_length=255, default="")
    position_detail = models.TextField(default="")

    def __str__(self):
        return f"{self.company_name} - {self.position}"
