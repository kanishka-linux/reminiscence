from django.urls import resolve, reverse
from django.test import TestCase
from pages.views import dashboard

class HomeTests(TestCase):
    
    def test_home_view_status_code(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

    def test_home_url_resolves_home_view(self):
        view = resolve('/')
        self.assertEquals(view.func, dashboard)

