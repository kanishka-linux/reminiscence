from django.contrib.auth.models import User
from django.test import TestCase, Client, tag
from django.urls import resolve, reverse
from pages.models import Library
from django.utils import timezone

class DRFTests(TestCase):
    
    client = Client()
    iurl = 'https://en.wikipedia.org/wiki/Main_Page'
    auth_token = None
    
    @classmethod
    def setUpTestData(cls):
        usr = User.objects.create_user(username='johndoe', password='clrsalgo')
        Library.objects.create(usr=usr, directory='TMP')
        Library.objects.create(usr=usr, directory='TMP', title='Wiki',
                               url=cls.iurl, timestamp=timezone.now())
    
    def setUp(self):
        url = reverse('get_auth_token')
        response = self.client.post(url, {'username': 'johndoe', 'password': 'clrsalgo'})
        self.auth_token = response.json().get('token')
        
    @tag('async')
    def test_add_url(self):
        url = reverse('add_url')
        post_data = {
            "url": "https://mr.wikipedia.org/wiki/Main_Page",
            "media_link": "no", "directory": "/TMP",
            "save_favicon": "no"
            }
        response = self.client.post(url, post_data, HTTP_AUTHORIZATION='Token {}'.format(self.auth_token))
        self.assertEquals(response.status_code, 200)
        
    def test_drf_list_directories(self):
        url = reverse('list_directories')
        response = self.client.get(url, HTTP_AUTHORIZATION='Token {}'.format(self.auth_token))
        self.assertEquals(response.status_code, 200)

    def test_drf_list_urls(self):
        url = reverse('list_added_urls')
        post_data = {"directory": "/TMP"}
        response = self.client.post(url, post_data, HTTP_AUTHORIZATION='Token {}'.format(self.auth_token))
        self.assertEquals(response.status_code, 200)

