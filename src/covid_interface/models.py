from django.db import models
import datetime
from django.utils import timezone
# Create your models here.


class Country(models.Model):
    location_name   = models.CharField(max_length=150, unique=True)
    est_population  = models.BigIntegerField()
    api_endpoint    = models.URLField()
    resource_url    = models.URLField()
    
    def __str__(self):
        return self.location_name

class Data(models.Model):
    key             =   models.OneToOneField(
                            Country,
                            on_delete=models.CASCADE,
                            primary_key=True,
                        )
    response_code   =   models.IntegerField()
    derived_data    =   models.JSONField()
    raw_data        =   models.JSONField()
    update_date     =   models.DateTimeField('date updated')

    def was_updated_recently(self):
        return self.update_date >= timezone.now() - datetime.timedelta(hours=12)