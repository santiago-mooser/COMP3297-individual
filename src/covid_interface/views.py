import json

import requests
from django.http.response import HttpResponse
from django.shortcuts import render
from django.template import loader

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

    # Otherwise, if the request is not post, the user is not 
    # submitting data, so the default view (Hong Kong) is shown
    else:
        #This is empty for now but imagine it to be similar to the 
        #above part but with Hong Kong hard-coded in
        loc_name = "Hong Kong"

    # This retrieves the location information from the Country that has the 
    # name "${loc_name}". This allows us to retrieved the stored API data
    # that was previously provided by the user
    location_info = Country.objects.filter(location_name=loc_name)
    

    # This is the part of the view that retrieves the data from the API (the query script), 
    # except that now, instead of using hardcoded data, the script uses data stored in the 
    # database (which is accessed using the Country model) 
    query = {
            "resource": location_info.resource_url,
            "section":  1,
            "format":   "json",
        }

    url = location_info.api_endpoint

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

            # Save the model to the DB
            model.save()

            #TODO: Add redirect to homepage of ${loc}


        # Else process the error in the form
        else:
            print("placeholder code")

    # Otherwise simply return the empty tempalte so users can imput data    
    return HttpResponse(template.render(context, request))

