from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class DashboardTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_renders_correctly(self):
        # Without login
        response = self.client.get(reverse('home:home'), follow=True)
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
        response = self.client.get(reverse('home:home'), follow=True)
        self.assertContains(response, "Apply methods",
                            status_code = 200)
