from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('album/<uuid:album_id>/', views.album_detail, name='album_detail'),
    path('',views.landing, name='landing'),
    path('landing/how it works/',views.works, name='works'),
    path('signup/',views.signup, name='signup'),
    path('albums/', views.my_albums, name='my_albums'),
    path('albums/create/', views.create_album, name='create_album'),

]
  