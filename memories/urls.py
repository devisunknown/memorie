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
    path(
    "album/<uuid:pk>/delete/",
    views.delete_album,
    name="delete_album",
),
    path('invites/', views.pending_invites, name='pending_invites'),
    path('invites/<int:share_id>/<str:action>/', views.respond_to_invite, name='respond_to_invite'),
    path('albums/<uuid:album_id>/share/', views.share_album, name='share_album'),
    path('join/<uuid:token>/', views.join_via_link, name='join_via_link'),
    path('albums/<uuid:album_id>/share/regenerate/', views.regenerate_share_link, name='regenerate_share_link'),
    path('albums/<uuid:album_id>/guest-requests/<int:request_id>/<str:action>/', views.respond_guest_request, name='respond_guest_request'),

]
  