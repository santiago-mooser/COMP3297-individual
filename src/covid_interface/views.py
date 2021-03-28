import json

import requests
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import loader
from django.utils import timezone
from django.contrib import messages
from .forms import *
from .models import *



# This is so that if the website is visited without any options, 
# the Hong Kong view will still be displayed.
def proxy(request):
    return redirect('homepage', loc_name='Hong Kong')



# This view allows the user to delete a view. It is hidden
# on purpose because it is not in the specs and although 
# I would usually never add out-of-spec, hidden features, 
# it is a pain in the ass to erase data in heroku's postgres
def delete(request, loc_name):
    try:
        loc = Country.objects.get(location_name=loc_name)
        loc.delete()
    except:
        return redirect('proxy')

    messages.info(request, f'{loc_name} deleted from database.')
    return redirect('proxy')



# Small easteregg for prof
def teapot(request):
    messages.info(request, "HTTP 418")

    return redirect('proxy')



# This simple view allows the user to manually update the page
def update(request, loc_name):

    #Try retrieving the object containing that country's information
    try:
        location_info = Country.objects.get(location_name=loc_name)

    #If it doesn't exist, redirect to default page
    except:
        return redirect('proxy')

    update_data(location_info, request)

    return redirect('homepage', loc_name=loc_name)



#This is the main homepage that actually presents all the data.
# It expects a location name in the form of a string.
def homepage(request, loc_name):

    # Load the HTML template and instantiate the context
    template = loader.get_template('views/homepage.html')
    context = {}
    
    #Get a list of all available countries (if any)
    try:
        countries = []
        for country in Country.objects.values():
            countries.append(country.get("location_name"))

    # If no countries exist in the DB, show "I f'd up" error
    except:
        context.update({"location_name": loc_name})
        template = loader.get_template('views/no_locations.html')
        messages.warning(request, "No locations saved!")
        return HttpResponse(template.render(context, request))

    context.update({
        "countries": countries
    })

    #retrieve location information if it exists
    try:
        location_info = Country.objects.get(location_name=loc_name)

    #If it doesn't exist, show a "you f'd up" error
    except:
        context.update({"countries": countries,
                        "location_name": loc_name})
        template = loader.get_template('views/no_locations.html')
        messages.warning(request, "Location not found!")
        return HttpResponse(template.render(context, request))

    # Add the location name to the context from request
    context.update({ "location_name": location_info.location_name })

    # retrieve dataset associated with the location
    try:
        data_set = location_info.data
    except ObjectDoesNotExist:
        messages.error(request, "Unable to retrieve details.")
        return HttpResponse(template.render(context, request))
    except:
        update_data(location_info, request)
        data_set = location_info.data

    # Update the data if it hasn't been updated in the last 24 hours
    if not data_set.data_is_updated:
        update_data(location_info, request)
        messages.info(request, "Success! Data updated.")

    # If the data was successfully retrieved, then add the data to 
    # the context
    if data_set.response_code == 200:
        context.update({
            "raw": data_set.raw_data,
            "derived": data_set.derived_data,
        })

    return HttpResponse(template.render(context, request))



# This view retrieves, processes and stores the API data in
# the database. It is *not* called through URLs, but from 
# the other views.
# This is why the request is here ↓
def update_data(country_model, request):

    # Retrieve data_set from the given country
    try:
       data_set = country_model.data
    
    except ObjectDoesNotExist:
        data_set = Data(
            key = country_model,
            response_code=0,    
            raw_data={}, 
            derived_data={},
            update_date=timezone.now()
        )

    # Create the query from the saved information
    query = {
        "resource": country_model.resource_url,
        "section":  1,
        "format":   "json",
    }

    # Run the query
    try:
        r =  requests.get(
                    country_model.api_endpoint,
                    params={
                        "q": json.dumps(query),
                    }
        )

    # If the query didn't succeed, return with an error 
    except:
        messages.error(request, "Data retrieval failed! Please check API status.")
        return

    # If the status code isn't 200, return with errors.
    if r.status_code != 200:
        
        data_set.response_code = r.status_code
        data_set.save()
        messages.error(request, "Non-standard response from API! Please check API status.")
        return 

    # Otherwise instatiate and populate the necessary variables 
    # to save the raw and derived data
    try:
        # Calculate all the needed data
        response = r.json()
        average_cases = 0
        average_fatalities = 0
        cases = 0
        deaths = 0
        for i in range(7):
            cases = int(response[-i-1].get("Number of confirmed cases")) - int(response[-i-2].get("Number of confirmed cases"))
            deaths = int(response[-i-1].get("Number of death cases")) - int(response[-i-2].get("Number of death cases"))
            average_cases += cases   
            average_fatalities += deaths       

        # Create the needed JSON objects
        raw = { 
            "date":{
                "label": "Data last updated", 
                "data":response[-1].get("As of date")},
            "total_cases": {
                "label": "Total Cases", 
                "data":response[-1].get("Number of confirmed cases")
            },
            "total_deaths":{
                "label": "Total Deaths", 
                "data":response[-1].get("Number of death cases")
            },
        }

        derived = { 
            "new_cases": {  
                "label": "Cases as of last update", 
                "data": cases,
            },
            "average_cases": { 
                "label": "7-Day rolling average of cases", 
                "data": int(average_cases/7),
            },
            "cases_per_mil": {  
                "label": "Cases per million people", 
                "data": int(response[-1].get("Number of confirmed cases")/(country_model.est_population/1000000)),
            },
            "new_deaths": {
                "label": "Deaths as of last update", 
                "data": deaths,
            },
            "average_fatalities": { 
                "label": "7-Day rolling average of deaths", 
                "data": int(average_fatalities/7),
            },
            "deaths_per_mil": {
                "label": "Deaths per million people", 
                "data": int(response[-1].get("Number of death cases")/(country_model.est_population/1000000)),
            },
        }

        # Save updates in dataset 
        try:
            data_set.response_code=r.status_code
            data_set.raw_data=raw
            data_set.derived_data=derived
            data_set.update_date=timezone.now()

            data_set.save()

        #If this fails the database is not accessible 
        except:
            messages(request, "Unable to store data in database. Please reload page.")

    # If the derived data can't be computed, the API must have sent bad
    # data. 
    except:
        messages.error(request, 'Data sent by API is not parseable. Please check location API.')
        return

    messages.success(request, "Data successfully updated.")
    return



def newResource_proxy(request):
    
    return redirect('newResource', loc_name="new")



# This view is for saving data. This is the only view where new 
# database objects can be created. 
def newResource(request, loc_name):

    # First, like always, load the HTML template with no context
    template = loader.get_template('views/new_resource.html')
    context = {}

    if loc_name == "new":
        form = newResourceForm(initial={"location_name": ""})
    else:
        form = newResourceForm(initial={"location_name": loc_name})
    context.update({ "form": form })

    #If the request is POST, process the form (since the user is submitting data)
    if request.method == "POST":
        form = newResourceForm(request.POST)

        #Check whether the form is valid
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
            try:
                model.save()
            
            # If that doesn't work, we probably have bigger problems
            except:
                messages.error(request, "Internal server error! Please reload page.")
                return HttpResponse(template.render(context, request))

            #Update the data
            update_data(model, request)

            # If all checks pass, return success & redirect to the country
            messages.success(request, "Details successfully saved.")
            return HttpResponseRedirect('/country/'+loc)

        # Else return a 400 (invalid request) to user
        else:
            messages.error(request, "Please enter valid details.")
            return redirect('newResource', loc_name=loc_name)
 
    return HttpResponse(template.render(context, request))

