import uuid
from django.db import models
from core.models import BaseModel

class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_id = models.CharField(max_length=50, unique=True)
    km = models.PositiveIntegerField()
    price = models.FloatField(help_text='Price of the vehicle')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    version = models.CharField(max_length=100, blank=True)
    bluetooth = models.BooleanField(default=False)
    car_play = models.BooleanField(default=False)
    largo = models.FloatField(help_text='Length of the vehicle')
    ancho = models.FloatField(help_text='Width of the vehicle')
    altura = models.FloatField(help_text='Height of the vehicle')
    

class KnowledgeArticle(BaseModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.TextField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name