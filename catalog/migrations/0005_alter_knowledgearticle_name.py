# Generated by Django 5.2.1 on 2025-05-21 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_alter_knowledgearticle_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='knowledgearticle',
            name='name',
            field=models.TextField(blank=True, null=True),
        ),
    ]
