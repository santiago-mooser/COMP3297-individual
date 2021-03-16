from django.urls import path

from . import views

urlpatterns = [
    path('', views.proxy, name='proxy'),
    path('country/', views.proxy, name='proxy'),
    path('country/<str:loc_name>', views.homepage, name='homepage'),
    path('add/', views.newResource, name='new_resource'),
]
