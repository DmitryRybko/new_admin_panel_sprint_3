# Generated by Django 3.2 on 2022-12-04 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personfilmwork',
            name='role',
            field=models.TextField(choices=[('FD', 'film director'), ('SW', 'screenwriter'), ('AC', 'actor')], null=True, verbose_name='role'),
        ),
    ]
