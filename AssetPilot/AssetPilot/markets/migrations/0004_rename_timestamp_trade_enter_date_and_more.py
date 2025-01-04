# Generated by Django 5.1.3 on 2025-01-04 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("markets", "0003_trade_is_open"),
    ]

    operations = [
        migrations.RenameField(
            model_name="trade",
            old_name="timestamp",
            new_name="enter_date",
        ),
        migrations.RenameField(
            model_name="trade",
            old_name="price",
            new_name="enter_price",
        ),
        migrations.AddField(
            model_name="trade",
            name="close_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="trade",
            name="close_price",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
    ]
