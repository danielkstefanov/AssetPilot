from django.db import models
import uuid


class NewsItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime = models.DateTimeField()
    headline = models.CharField(max_length=500)
    summary = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    sentiment_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    is_positive = models.BooleanField(null=True, blank=True)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500)
    source = models.CharField(max_length=200)
