from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib import auth


class CreateUserTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_create_user(self):
        self.client.post(reverse('user:create'),
                           {'username' : 'hans_wurst',
                            'email': 'hans.wurst@gmail.com',
                            'first_name': 'Hans',
                            'last_name': 'Wurst',
                            'organisation': 'Wurst Gmbh',
                            'type_of_use': 'commercial',
                            'password1' : 'Musterpasswort2018',
                            'password2': 'Musterpasswort2018'})
        user = auth.get_user(self.client)
        assert user.is_authenticated()


class LoginUserTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.client.post(reverse('user:create'),
                           {'username' : 'hans_wurst',
                            'email': 'hans.wurst@gmail.com',
                            'first_name': 'Hans',
                            'last_name': 'Wurst',
                            'organisation': 'Wurst Gmbh',
                            'type_of_use': 'commercial',
                            'password1' : 'Musterpasswort2018',
                            'password2': 'Musterpasswort2018'})

    def test_login(self):
        self.client.post(reverse('user:authentication'),
                               {'username' : 'hans_wurst',
                                'password' : 'Musterpasswort2018'})
        user = auth.get_user(self.client)
        assert user.is_authenticated()
