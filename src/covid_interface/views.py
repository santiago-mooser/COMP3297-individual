import json

import requests
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.core.exceptions import ObjectDoesNotExist, FieldError
from .forms import *
from .models import *


# This is so that if the website is visited without any options, 
# the Hong Kong view will still be displayed.
def proxy(request):
    return homepage(request, "Hong Kong")


#This is the main homepage that actually presents all the data
# It expects the request together with a location name in the 
# form of a string.
def homepage(request, loc_name):

    # Load the HTML template and instantiate context
    template = loader.get_template('views/homepage.html')
    context = {}

    #Get a list of all available countries
    countries = []
    for country in Country.objects.values():
        countries.append(country.get("location_name"))

    #retrieve location information if it exists
    try:
        location_info = Country.objects.get(location_name=loc_name)

    #If it doesn't, deal with the errors
    except ObjectDoesNotExist:
        context.update({"error": "404", 
                        "countries": countries,
                        "location_name": loc_name})
        return HttpResponse(template.render(context, request))


    context.update({ "location_name": location_info.location_name })

    query = {
            "resource": location_info.resource_url,
            "section":  1,
            "format":   "json",
        }

    url = location_info.api_endpoint

    response = requests.get(url, params={"q": json.dumps(query)} )

    # If the status code isn't 200 (meaning success), then there was an error in the 
    # retrieval of information so we must tell the user. 
    if response.status_code != 200:
        
        context.update({"error": response.status_code,
                        "location_name": location_info.location_name,})

        HttpResponse(template.render(context, request))

    response = response.json()
    average_cases = 0
    average_fatalities = 0
    cases = 0
    deaths = 0
    for i in range(7):
        cases = int(response[-i-1].get("Number of confirmed cases")) - int(response[-i-2].get("Number of confirmed cases"))
        deaths = int(response[-i-1].get("Number of death cases")) - int(response[-i-2].get("Number of death cases"))
        average_cases += cases   
        average_fatalities += deaths       


    context.update({
                    "location_name": location_info.location_name,
                    "countries": countries,
                    "derived": {
                        "cases": cases,
                        "average_cases": average_cases/7,
                        "deaths": deaths,
                        "average_fatalities": average_fatalities/7,
                        },
                    "raw":{
                        "date": response[-1].get("As of date"),
                        "total_cases": response[-1].get("Number of confirmed cases"),
                        "total_deaths": response[-1].get("Number of death cases"),
                        },
                    })
    
    print(context)

    # Otherwise, we can return the homepage HTML template with the retrieved data.
    return HttpResponse(template.render(context, request))



# In this page, the user is saving data
def newResource(request):

    # First, like always, load the HTML template with no context
    template = loader.get_template('views/new_resource.html')
    context = {}

    #If the request is POST, process the form (since the user is submitting data)
    if request.method == "POST":
        form = newResourceForm(request.POST)

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
            
            # If all checks pass, redirect to the country
            return HttpResponseRedirect('/country/'+loc)

        # Else return a 400 (invalid request) to user
        else:
            context = {"error": "400"}
            return HttpResponse(template.render(context, request))

    # Otherwise simply return the empty tempalte so users can imput data  
    model = Country
    form = newResourceForm()
    context.update({ "form": form }) 

    print("Returning form")
    return HttpResponse(template.render(context, request))

