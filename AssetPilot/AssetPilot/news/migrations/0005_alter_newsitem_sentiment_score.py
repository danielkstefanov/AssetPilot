# Generated by Django 5.1.3 on 2025-01-20 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0004_alter_newsitem_sentiment_score"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsitem",
            name="sentiment_score",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True
            ),
        ),
    ]
