# Generated by Django 4.2.10 on 2024-02-23 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_alter_user_date_created"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="date_created",
            field=models.DateTimeField(db_index=True, verbose_name="date created"),
        ),
    ]