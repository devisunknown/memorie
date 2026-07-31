from django.urls import path
from . import views

urlpatterns = [
    path('oslogin/', views.oslogin, name='oslogin'),
    path('', views.osei, name='osei'),
]
  