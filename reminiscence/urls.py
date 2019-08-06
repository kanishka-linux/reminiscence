"""helloworld URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
#from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.urls import re_path as url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

if settings.ROOT_URL_LOCATION:
    root_loc = settings.ROOT_URL_LOCATION
    if root_loc.startswith('/'):
        root_loc = root_loc[1:]
    if not root_loc.endswith('/'):
        root_loc = root_loc + '/'
    root_loc = '^' + root_loc
    custom_loc = root_loc
else:
    root_loc = ''
    custom_loc = '^'
    
urlpatterns = [
    url(r'{}admin/'.format(custom_loc), admin.site.urls),
    url(r'{}restapi/'.format(custom_loc), include('restapi.urls')),
    url(r'{}'.format(root_loc), include('pages.urls')),
]

urlpatterns += staticfiles_urlpatterns()
