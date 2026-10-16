from django.contrib import admin
from .models import Transcript
@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ("id", "owner_key", "created_at")
    search_fields = ("original_text", "corrected_text")
