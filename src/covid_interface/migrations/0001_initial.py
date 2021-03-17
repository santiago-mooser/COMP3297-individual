# Generated by Django 3.1.7 on 2021-03-12 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_name', models.CharField(max_length=150, unique=True)),
                ('est_population', models.BigIntegerField()),
                ('api_endpoint', models.URLField()),
                ('resource_url', models.URLField()),
            ],
        ),
    ]