from django.urls import path

from . import views

app_name = "resume"

urlpatterns = [
    path("mypage/profile/", views.replace_profile_info, name="replace_profile_info"),
]
