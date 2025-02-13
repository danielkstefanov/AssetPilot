from django.db import models
import uuid


class NewsItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime = models.DateTimeField(null=True, blank=True)
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

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    models.Q(is_positive=True, sentiment_score__gte=0)
                    | models.Q(is_positive=False, sentiment_score__lt=0)
                ),
                name="sentiment_score_check",
            ),
            models.CheckConstraint(
                check=(
                    (models.Q(sentiment_score__gte=-100) & models.Q(sentiment_score__lte=100))
                    | models.Q(sentiment_score__isnull=True)
                ),
                name="sentiment_score_is_in_range_from_-100_to_100",
            ),
        ]
