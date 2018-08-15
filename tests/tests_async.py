import unittest
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import resolve, reverse
from pages.models import Library
from pages.views import dashboard


class LibraryTests(unittest.TestCase):
    
    client = Client()
    
    def setUp(self):
        usr = User.objects.create_user(username='njohndoe', password='clrsalgo')
        Library.objects.create(usr=usr, directory='TMP')
        self.client.login(username='njohndoe', password='clrsalgo')
    
    def test_add_url(self):
        url = reverse('navigate_directory', kwargs={'username': 'njohndoe', 'directory': 'TMP'})
        response = self.client.post(url, {'add_url':'https://en.wikipedia.org/wiki/Main_Page'})
        self.assertEquals(response.status_code, 200)
