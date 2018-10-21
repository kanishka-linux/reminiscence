from django.contrib.auth.forms import UserCreationForm
from django.urls import resolve, reverse
from django.test import TestCase
from accounts.views import signup
from django.conf import settings


class SignUpTests(TestCase):
    
    def setUp(self):
        url = reverse('signup')
        self.response = self.client.get(url)

    def test_signup_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        view = resolve('{}/signup/'.format(settings.ROOT_URL_LOCATION))
        self.assertEquals(view.func, signup)

    def test_csrf(self):
        if settings.ALLOW_ANY_ONE_SIGNUP:
            self.assertContains(self.response, 'csrfmiddlewaretoken')
        else:
            self.assertContains(self.response, 'New sign up not allowed')

    def test_contains_form(self):
        if settings.ALLOW_ANY_ONE_SIGNUP:
            form = self.response.context.get('form')
            self.assertIsInstance(form, UserCreationForm)
        else:
            self.assertContains(self.response, 'New sign up not allowed')
