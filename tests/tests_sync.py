from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import resolve, reverse
from pages.models import Library
from pages.views import dashboard
from django.utils import timezone


class LibraryTests(TestCase):
    
    client = Client()
    url = 'https://en.wikipedia.org/wiki/Main_Page'
    
    @classmethod
    def setUpTestData(cls):
        usr = User.objects.create_user(username='johndoe', password='clrsalgo')
        Library.objects.create(usr=usr, directory='TMP')
        Library.objects.create(usr=usr, directory='TMP', title='Wiki',
                               url=cls.url, timestamp=timezone.now())
    
    def setUp(self):
        self.client.login(username='johndoe', password='clrsalgo')

    def test_dashboard_page(self):
        url = reverse('home_page', kwargs={'username': 'johndoe'})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
    
    def test_add_directory(self):
        url = reverse('home_page', kwargs={'username': 'johndoe'})
        response = self.client.post(url, {'create_directory':'Sample'})
        self.assertEquals(response.status_code, 200)
        
    def test_check_url(self):
        url = reverse('navigate_directory', kwargs={'username': 'johndoe', 'directory': 'TMP'})
        response = self.client.get(url)
        self.assertContains(response, self.url)
    
    
