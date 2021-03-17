from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import *


class newResourceForm(forms.Form):
    location_name   = forms.CharField(max_length=150, label='Location name')
    est_population  = forms.IntegerField(label='Estimated Population')
    api_endpoint    = forms.URLField(label='API Endpoint')
    resource_url    = forms.URLField(label='Resource URL')

    class Meta:
        model = Country
        fields = ('location_name', 'est_population', 'api_endpoint', 'resource_url')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save information'))
