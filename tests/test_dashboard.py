from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class DashboardTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_renders_correctly(self):
        # Without login
        response = self.client.get(reverse('contour:index'), follow=True)
        self.assertContains(response, "Please login to use ViroCon",
                            status_code = 200)

        # With login
        self.client.post(reverse('user:authentication'),
                           {'username' : 'max_mustermann',
                            'password' : 'Musterpasswort2018'})
        response = self.client.get(reverse('contour:index'), follow=True)
        self.assertContains(response, "Apply methods",
                            status_code = 200)
