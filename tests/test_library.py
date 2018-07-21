from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse

from pages.models import Library
from pages.views import dashboard


class NewTopicTests(TestCase):
    
    def setUp(self):
        usr = User.objects.create_user(username='johndoe', password='clrsalgo')
        Library.objects.create(usr=usr, title='wikipedia',
                               directory='TMP',
                               url='https://en.wikipedia.org/wiki/Main_Page')
        self.client.login(username='johndoe', password='clrsalgo')

    def test_dashboard_page(self):
        url = reverse('home_page', kwargs={'username': 'johndoe'})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

