from django import forms


class homePageForm(forms.Form):
    location = forms.CharField(max_length=100)

class newResourceForm(forms.Form):
    location_name   = forms.CharField(max_length=150, unique=True)
    est_population  = forms.IntegerField()
    api_endpoint    = forms.URLField()
    resource_url    = forms.URLField()