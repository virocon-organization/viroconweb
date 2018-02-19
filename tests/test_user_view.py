from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class UserTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_edit_user(self):

        # Without login
        response = self.client.get(reverse('user:edit'), follow=True)
        self.assertContains(response, "Please login to use ViroCon",
                            status_code = 200)

        # With login
        self.client.post(reverse('user:create'),
                           {'username' : 'max_mustermann',
                            'email' : 'max.mustermann@gmail.com',
                            'first_name' : 'Max',
                            'last_name' : 'Mustermann',
                            'organisation' : 'Musterfirma',
                            'type_of_use' : 'commercial',
                            'password1' : 'Musterpasswort2018',
                            'password2' : 'Musterpasswort2018'})
        response = self.client.get(reverse('user:edit'), follow=True)
        self.assertContains(response, "Edit",
                            status_code = 200)

    def test_change_password(self):

        # Without login
        response = self.client.get(reverse('user:change-password'), follow=True)
        self.assertContains(response, "Please login to use ViroCon",
                            status_code = 200)

        # With login
        self.client.post(reverse('user:create'),
                           {'username' : 'max_mustermann',
                            'email' : 'max.mustermann@gmail.com',
                            'first_name' : 'Max',
                            'last_name' : 'Mustermann',
                            'organisation' : 'Musterfirma',
                            'type_of_use' : 'commercial',
                            'password1' : 'Musterpasswort2018',
                            'password2' : 'Musterpasswort2018'})
        response = self.client.get(reverse('user:change-password'), follow=True)
        self.assertContains(response, "Edit",
                            status_code = 200)

    def test_show_user_profile(self):

        # Without login
        response = self.client.get(reverse('user:profile'), follow=True)
        self.assertContains(response, "Please login to use ViroCon",
                            status_code = 200)

        # With login
        self.client.post(reverse('user:create'),
                           {'username' : 'max_mustermann',
                            'email' : 'max.mustermann@gmail.com',
                            'first_name' : 'Max',
                            'last_name' : 'Mustermann',
                            'organisation' : 'Musterfirma',
                            'type_of_use' : 'commercial',
                            'password1' : 'Musterpasswort2018',
                            'password2' : 'Musterpasswort2018'})
        response = self.client.get(reverse('user:profile'), follow=True)
        self.assertContains(response, "Mustermann",
                            status_code = 200)
