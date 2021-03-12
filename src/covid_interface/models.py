from django.db import models

# Create your models here.


class Country(models.Model):
    location_name   = models.CharField(max_length=150, unique=True)
    est_population  = models.BigIntegerField()
    api_endpoint    = models.URLField()
    resource_url    = models.URLField()