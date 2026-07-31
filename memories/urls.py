from django.urls import path
from . import views

urlpatterns = [
    path('', views.osei, name='osei'),
    path('login/', views.oslogin, name='oslogin'),
]