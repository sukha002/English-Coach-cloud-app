from django.db import models

class Transcript(models.Model):
    # Anonymous browser-scoped key, not a secure account identity.
    owner_key = models.CharField(max_length=80, db_index=True)
    original_text = models.TextField()
    corrected_text = models.TextField()
    corrections = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
