from django.urls import path

from . import views

urlpatterns = [
    path('', views.proxy, name='proxy'),
    path('country/', views.proxy, name='proxy'),
    path('country/<str:loc_name>', views.homepage, name='homepage'),
    path('delete/<str:loc_name>', views.delete, name='delete'),
    path('update/<str:loc_name>', views.update, name='update'),
    path('add/', views.newResource, name='new_resource'),
]
