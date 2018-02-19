from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class HelpTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_renders_correctly(self):
        response = self.client.get(reverse('contact:help'), follow=True)
        self.assertContains(response, "Help",
                            status_code = 200)
