import json

import requests
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import loader
from django.utils import timezone
from .forms import *
from .models import *



# This is so that if the website is visited without any options, 
# the Hong Kong view will still be displayed.
def proxy(request):
    return redirect('homepage', loc_name='Hong Kong')



def delete(request, loc_name):
    try:
        loc = Country.objects.get(location_name=loc_name)
        loc.delete()
    except:
        return redirect('proxy')
    return redirect('proxy')



def update(request, loc_name):
    try:
        location_info = Country.objects.get(location_name=loc_name)

    #If it doesn't exist, deal with the errors
    except:
        return redirect('proxy')

    try:
        update_data(location_info)
    except:
        print("Update failed!")

    return redirect('homepage', loc_name=loc_name)



#This is the main homepage that actually presents all the data
# It expects the request together with a location name in the 
# form of a string.
def homepage(request, loc_name):

    # Load the HTML template and instantiate context
    template = loader.get_template('views/homepage.html')
    context = {}
    
    #Get a list of all available countries
    try:
        countries = []
        for country in Country.objects.values():
            countries.append(country.get("location_name"))

    # If no countries exist in the DB, give a 404 error
    except:
        context.update({"error": "404",
                        "location_name": loc_name})
        return HttpResponse(template.render(context, request))

    context.update({
        "countries": countries
    })

    #retrieve location information if it exists
    try:
        location_info = Country.objects.get(location_name=loc_name)

    #If it doesn't exist, deal with the errors
    except:
        context.update({"error": "404", 
                        "countries": countries,
                        "location_name": loc_name})
        return HttpResponse(template.render(context, request))

    context.update({ "location_name": location_info.location_name })

    # retrieve dataset associated with the location
    try:
        data_set = location_info.data
    except:
        try:
            update_data(location_info)
        except:
            print("Update failed")
        data_set = location_info.data

    # Update the data if it hasn't been updated in the last 24 hours
    if not data_set.data_is_updated:
        try:
            update_data(location_info)
        except:
            print("Failed update!")

    # If the data was successfully retrieved, then display the data
    if data_set.response_code == 200:
        context.update({
            "raw": data_set.raw_data,
            "derived": data_set.derived_data,
        })
    else:
        context.update({
            "error": data_set.response_code,
        })

    # Otherwise, we can return the homepage HTML template with the retrieved data.
    return HttpResponse(template.render(context, request))



def update_data(country_model):

    # Retrieve data_set from the given country
    # If it doesn't exist, create a new one 
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

    # Format the query
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
    except:
        print("Update failed!")
        return

    # If the status code isn't 200 (meaning success), then there was an error in the 
    # retrieval of information so we must tell the user. 
    if r.status_code != 200:
        
        data_set.response_code = r.status_code
        data_set.save()  
        return 

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
                "label": "Date", 
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
                "label": "New Cases today", 
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
                "label": "New deaths today", 
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
        data_set.response_code=r.status_code
        data_set.raw_data=raw
        data_set.derived_data=derived
        data_set.update_date=timezone.now()

        data_set.save()
        print("Updated!")

    except:
        print("Update failed.")
    
    print("Updated!")

    return



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

            # Update the data
            try:
                update_data(model)
            except:
                print("Update failed")

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
    return HttpResponse(template.render(context, request))

