from django.urls import path

from . import views

urlpatterns = [
    #Redirect default views to HK
    path('', views.proxy, name='proxy'),
    path('country/', views.proxy, name='proxy'),

    #Path to add a new resource
    path('add/', views.newResource_proxy, name='new_resource_proxy'),
    path('add/<str:loc_name>', views.newResource, name='newResource'),

    # Once those resources have been added, you can see,
    # delete or update them, or anjoy a nice cup of tea.
    path('country/<str:loc_name>', views.homepage, name='homepage'),
    path('delete/<str:loc_name>', views.delete, name='delete'),
    path('update/<str:loc_name>', views.update, name='update'),
    path('418/', views.teapot, name="teapot")
]
