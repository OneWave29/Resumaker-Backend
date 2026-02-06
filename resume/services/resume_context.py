#db에 있는 마이페이지 정보를 json으로 빌더하는 파일
from typing import Dict, Any

from resume.models import Award, Education, Certification, WorkExperience  # 경로 수정


def build_db_context(user) -> Dict[str, Any]:
    awards = Award.objects.filter(user_id=user.id).values(
        "id", "user_id", "competition_name", "award_title", "award_year", "awarding_organization"
    )

    educations = Education.objects.filter(user_id=user.id).values(
        "id", "user_id", "university", "major", "enrollment_year", "graduation_year", "gpa"
    )

    certifications = Certification.objects.filter(user_id=user.id).values(
        "id", "user_id", "obtained_date", "issuing_organization", "score", "grade"
    )

    work_experiences = WorkExperience.objects.filter(user_id=user.id).values(
        "id", "user_id", "company_name", "start_year", "end_year", "job_title", "job_description"
    )

    return {
        "awards": list(awards),
        "educations": list(educations),
        "certifications": list(certifications),
        "work_experiences": list(work_experiences),
    }
