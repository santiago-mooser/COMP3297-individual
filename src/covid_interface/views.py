import json

import requests
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.core.exceptions import ObjectDoesNotExist, FieldError
from .forms import *
from .models import *

# Create your views here.

def homepage(request):

    # Load the HTML template
    template = loader.get_template('views/homepage.html')
    
    # Context is any dynamic data in the HTML template (such as the name of 
    # the location and its data)
    context = {}

    # When the request to the "homepage" view is POST, this means that 
    # the user is trying to submit data, so we have to process the 
    # data in the request by using a form. In this case it's the 
    # location name only
    if request.method == "POST":
        form = homePageForm(request.POST)
        
        loc_name = form.cleaned_data["location_namee"]
        
        
        # This retrieves the location information from the Country that has the 
        # name "${loc_name}". This allows us to retrieved the stored API data
        # that was previously provided by the user
        try:
            location_info = Country.objects.filter(location_name=loc_name)

        except ObjectDoesNotExist:
            context = {"error": "404"}
            HttpResponse(template.render(context, request))

        query = {
                "resource": location_info.resource_url,
                "section":  1,
                "format":   "json",
            }

        url = location_info.api_endpoint

    else:
        loc_name = "Hong Kong"
        query = {
                "resource": "",
                "section":  1,
                "format":   "json",
        }
        url = "https://api.data.gov.hk/v2/filter"


    response = requests.get(url, params={"q": json.dumps(query)} )

    # If the status code isn't 200 (meaning success), then there was an error in the 
    # retrieval of information so we must tell the user. 
    if response.status_code != "200":
        
        context = { "error": response.status_code }

        HttpResponse(template.render(context, request))

    context = response.json()

    # Otherwise, we can return the homepage HTML template with the retrieved data.
    return HttpResponse(template.render(context, request))



# In this page, the user is saving data
def newResource(request):

    # First, like always, load the HTML template with no context
    template = loader.get_template('views/new_resource.html')
    context = {}

    #If the request is POST, process the form (since the user is submitting data)
    if request.method == "POST":
        form = homePageForm(request.POST)

        if form.is_valid():

            # Extract data from form
            loc     = form.cleaned_data["location_name"]
            pop     = form.cleaned_data["est_population"]
            api     = form.cleaned_data["api_endpoint"]
            url     = form.cleaned_data["resource_url"]

            # Create a new model with the data
            model = Country(location_name=loc,
                            est_population=pop,
                            api_endpoint=api,
                            resource_url=url)

            # Save the model to the DB. Return error if unable to do so
            try:
                model.save()
            except FieldError:
                context = {"error": "503"}
                return HttpResponse(template.render(context, request))
            
            # If all checks pass, redirect to home
            return HttpResponseRedirect('/')

        # Else return a 400 (invalid request) to user
        else:
            context = {"error": "400"}
            return HttpResponse(template.render(context, request))

    # Otherwise simply return the empty tempalte so users can imput data    
    return HttpResponse(template.render(context, request))

