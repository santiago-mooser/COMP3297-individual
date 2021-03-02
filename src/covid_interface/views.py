from django.http.response import HttpResponse
from django.shortcuts import render
from django.template import loader

# Create your views here.

def homepage(request):

    template = loader.get_template('views/homepage.html')
    context = {}
    return HttpResponse(template.render(context, request))