from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    path('add-url/', views.AddURL.as_view(), name='add_url'),
    path('list-directories/', views.ListDirectories.as_view(), name='list_directories'),
    path('list-added-urls/', views.ListURL.as_view(), name='list_added_urls'),
    path('login/', obtain_auth_token, name='get_auth_token'),
    path('logout/', views.Logout.as_view(), name='delete_auth_token'),
]
