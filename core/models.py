# Create your models here.
from django.db import models
from django.utils import timezone

class BaseModel(models.Model):
    """Abstract base model with created/updated timestamps."""
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Always update the `date_updated` timestamp on save
        self.date_updated = timezone.now()
        return super().save(*args, **kwargs)