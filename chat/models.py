import uuid
from django.db import models
from core.models import BaseModel


class Channel(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=255, unique=True)

class Message(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField()
    author = models.CharField(max_length=255, blank=True, null=True)