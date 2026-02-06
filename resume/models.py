from django.db import models
from users.models import User


class Education(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="educations",
        db_column="user_id",
    )
    university = models.CharField(max_length=255)
    major = models.CharField(max_length=255)
    enrollment_year = models.IntegerField()
    graduation_year = models.IntegerField()
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "education"


class Award(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="awards",
        db_column="user_id",
    )
    competition_name = models.CharField(max_length=255)
    award_title = models.CharField(max_length=255)
    award_year = models.IntegerField()
    awarding_organization = models.CharField(max_length=255)

    class Meta:
        db_table = "award"


class Certification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="certifications",
        db_column="user_id",
    )
    name = models.CharField(max_length=255)
    obtained_date = models.DateField()
    issuing_organization = models.CharField(max_length=255)
    score = models.IntegerField(null=True, blank=True)
    grade = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "certification"


class WorkExperience(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="work_experiences",
        db_column="user_id",
    )
    company_name = models.CharField(max_length=255)
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)
    job_title = models.CharField(max_length=255)
    job_description = models.TextField()

    class Meta:
        db_table = "work_experience"
