# Generated by Django 5.1.3 on 2025-02-13 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0006_newsitem_sentiment_score_check_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="newsitem",
            name="sentiment_score_is_in_range_from_-1_to_1",
        ),
        migrations.AddConstraint(
            model_name="newsitem",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("sentiment_score__gte", -100), ("sentiment_score__lte", 100)
                    ),
                    ("sentiment_score__isnull", True),
                    _connector="OR",
                ),
                name="sentiment_score_is_in_range_from_-100_to_100",
            ),
        ),
    ]
