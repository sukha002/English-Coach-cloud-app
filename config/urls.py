from django.contrib import admin
from django.urls import path
from coach import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("api/analyze/", views.analyze, name="analyze"),
    path("api/transcripts/", views.transcripts, name="transcripts"),
]
