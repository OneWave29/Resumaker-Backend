from django.conf import settings
from django.db import models


class Resume(models.Model):
    """
    Resume
    - id (PK)
    - user_id (FK)
    - item_list: Element id들의 순서를 저장하는 리스트(JSON)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
        db_column="user_id",  # DB 컬럼명이 user_id라면
    )

    # ERD에서 NULL 허용인데, 실제로 리스트로 쓰려면 default=list 추천
    item_list = models.JSONField(default=list, blank=True, null=True, db_column="item_list")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resume(id={self.id}, user_id={self.user_id})"


class Element(models.Model):
    """
    Element
    - id (PK)
    - resume_id (FK)
    - type (SIMPLE / TITLED)
    """
    class ElementType(models.TextChoices):
        SIMPLE = "SIMPLE", "SIMPLE"   # 단순내용(content)
        TITLED = "TITLED", "TITLED"   # 부제목+내용(content_subtitle)

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="elements",
        db_column="resume_id",
    )

    # ERD에서 type NULL 허용이면 null/blank True
    type = models.CharField(
        max_length=10,
        choices=ElementType.choices,
        null=True,
        blank=True,
        db_column="type",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Element(id={self.id}, resume_id={self.resume_id}, type={self.type})"


class Content(models.Model):
    """
    content (단순내용)
    - id (PK, 따로 존재)
    - element_id (FK/UK) -> Element (1:1)
    - content (text)
    """
    element = models.OneToOneField(
        Element,
        on_delete=models.CASCADE,
        related_name="simple_content",
        db_column="element_id",
    )

    content = models.TextField(null=True, blank=True, db_column="content")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Content(id={self.id}, element_id={self.element_id})"


class ContentSubtitle(models.Model):
    """
    content_subtitle (부제목+내용)
    - id (PK, 따로 존재)
    - element_id (FK/UK) -> Element (1:1)
    - sub_title
    - content
    """
    element = models.OneToOneField(
        Element,
        on_delete=models.CASCADE,
        related_name="titled_content",
        db_column="element_id",
    )

    sub_title = models.CharField(max_length=255, null=True, blank=True, db_column="sub_title")
    content = models.TextField(null=True, blank=True, db_column="content")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ContentSubtitle(id={self.id}, element_id={self.element_id})"
