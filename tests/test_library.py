from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse

from pages.models import Library
from pages.views import dashboard


class LibraryTests(TestCase):
    
    def setUp(self):
        usr = User.objects.create_user(username='johndoe', password='clrsalgo')
        Library.objects.create(usr=usr, directory='TMP')
        self.client.login(username='johndoe', password='clrsalgo')

    def test_dashboard_page(self):
        url = reverse('home_page', kwargs={'username': 'johndoe'})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_add_directory(self):
        url = reverse('home_page', kwargs={'username': 'johndoe'})
        response = self.client.post(url, {'create_directory':'Sample'})
        self.assertEquals(response.status_code, 200)
        
    def test_add_url(self):
        url = reverse('navigate_directory', kwargs={'username': 'johndoe', 'directory': 'TMP'})
        response = self.client.post(url, {'add_url':'https://en.wikipedia.org/wiki/Main_Page'})
        self.assertEquals(response.status_code, 200)

