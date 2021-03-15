from django import forms
from .models import *


class homePageForm(forms.Form):
    location_list = forms.ModelChoiceField(queryset=Country.objects.all().order_by('location_name'))


class newResourceForm(forms.Form):
    location_name   = forms.CharField(max_length=150)
    est_population  = forms.IntegerField()
    api_endpoint    = forms.URLField()
    resource_url    = forms.URLField()